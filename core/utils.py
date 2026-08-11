from django.utils.text import slugify


def unique_slugify(instance, value, slug_field_name="slug"):
    """Generate a unique slug for `instance`, appending -1, -2, ... on collision."""
    model = instance.__class__
    base_slug = slugify(value)
    slug = base_slug
    counter = 1
    while (
        model.objects.filter(**{slug_field_name: slug}).exclude(pk=instance.pk).exists()
    ):
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
