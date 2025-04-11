from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils.safestring import mark_safe
from .models import Book, Sketch, UserColor
import json, base64
import random

# Generate a random hex color
def get_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


@login_required
def dashboard(request):
    my_books = Book.objects.all()
    shared_books = request.user.collaborating_books.all()
    return render(request, "dashboard.html", {
        "my_books": my_books,
        "shared_books": shared_books
    })


@login_required
def create_book(request):
    if request.method == "POST":
        title = request.POST.get("title")
        book = Book.objects.create(name=title, created_by=request.user)
        return redirect(f"/book/{book.id}/")
    return render(request, "create_book.html")


@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.user != book.created_by and request.user not in book.collaborators.all():
        return JsonResponse({"error": "Unauthorized"}, status=403)
    return render(request, "book_detail.html", {
        "book": book,
        "sketches": book.sketches.all()
    })


@login_required
def sketch_room(request, sketch_id):
    sketch = get_object_or_404(Sketch, id=sketch_id)
    book = sketch.book

    if request.user != book.created_by and request.user not in book.collaborators.all():
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # Assign or fetch color
    user_color_obj, created = UserColor.objects.get_or_create(
        user=request.user,
        book=book,
        defaults={"color": get_random_color()}
    )

    strokes_json = mark_safe(json.dumps(sketch.strokes or []))

    return render(request, "sketch.html", {
        "sketch_id": sketch.id,
        "sketch_name": sketch.name,
        "saved_strokes_json": strokes_json,
        "user_color": user_color_obj.color,
        "user_id": request.user.id,
    })


@login_required
def create_sketch(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.user != book.created_by and request.user not in book.collaborators.all():
        return HttpResponseForbidden("You don't have permission to add sketches to this book.")

    if request.method == "POST":
        name = request.POST.get("name")
        sketch = Sketch.objects.create(name=name, book=book, created_by=request.user)
        return redirect(f"/sketch/{sketch.id}/")

    return render(request, "create_sketch.html", {"book": book})


@csrf_exempt
@login_required
def save_sketch(request):
    if request.method != 'POST':
        return JsonResponse({"status": "invalid_method"}, status=405)

    try:
        data = json.loads(request.body)
        sketch_id = data.get("id")
        new_name = data.get("name")
        image_data = data.get("image", "")
        strokes = data.get("strokes", [])

        # Fetch the sketch
        sketch = Sketch.objects.get(id=sketch_id)

        # Update name if provided
        if new_name:
            sketch.name = new_name

        # Handle image replacement
        if image_data and image_data.startswith("data:image/png;base64,"):
            image_data = image_data.replace("data:image/png;base64,", "")
            decoded_image = base64.b64decode(image_data)

            # Delete old image (if any)
            if sketch.image and sketch.image.name:
                sketch.image.delete(save=False)

            # Save new image with same name
            filename = f"sketches/{sketch.book}_sk_{sketch_id}.png"
            sketch.image.save(filename, ContentFile(decoded_image), save=False)

        # Update strokes
        sketch.strokes = strokes
        sketch.save()

        return JsonResponse({
            "status": "updated",
            "id": sketch.id,
            "name": sketch.name,
        })

    except Sketch.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Sketch not found."}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def clear_sketch(request, sketch_id):
    if request.method == 'POST':
        try:
            sketch = Sketch.objects.get(id=sketch_id)
            sketch.strokes = []  # Clear strokes only
            sketch.save()
            return JsonResponse({'success': True})
        except Sketch.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Sketch not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
from .gemini import prep_image, extract_text_from_image
@csrf_exempt
def upload_sketch_screenshot(request, sketch_id):
    if request.method == 'POST':
        sketch = get_object_or_404(Sketch, id=sketch_id)
        print("enter upload function")

        if not sketch.image:
            return JsonResponse({"error": "No image found."}, status=400)

        # Step 1: Get the book
        book = sketch.book

        # Step 2: Get all collaborators and their colors
        user_colors = UserColor.objects.filter(book=book)
        color_info = [
            f"{uc.user.username} used color {uc.color}" for uc in user_colors
        ]
        color_info_str = "\n".join(color_info)

        # Step 3: Prepare image
        local_image_path = sketch.image.path
        sample_file = prep_image(local_image_path)

        # Step 4: Create prompt with color info
        prompt = (
            "You're analyzing a sketch which contains handwritten math or science problems. "
            "Try to interpret the equations and expressions drawn. "
            "Here are the users and their assigned colors:\n\n"
            f"{color_info_str}\n\n"
            "Based on this, try to interpret what was written or solved in the sketch mention and correct each others mistake if there any."
        )

        # Step 5: Extract text using prompt
        text = extract_text_from_image(sample_file, prompt)
        text_list = text.split("\n")

        return JsonResponse({"text": text_list})

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)