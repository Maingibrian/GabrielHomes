# Mombasa presentation content

The redesigned home and listings pages support three markets: homes for sale,
long-term rentals, and short stays / BnB. The eight bundled presentation
listings are fictional and are always saved with `is_demo=True`.

For a fresh presentation database, after migrations:

```bash
python manage.py seed_demo --target 8 --i-know-this-is-demo
```

For an existing database that already contains the reference locations,
property types and agent profiles:

```bash
python manage.py seed_mombasa_showcase --i-know-this-is-demo
```

The second command is idempotent and never deletes owner data. The owner can
edit or replace every record in the custom dashboard. Once genuine inventory
is ready, use the existing **Hide demo data** switch in Site Content to remove
all presentation listings from the public site in one action.

## Stock presentation images

The bundled images are presentation placeholders downloaded from Unsplash and
used under the Unsplash License. Source pages:

- https://unsplash.com/photos/a-bright-and-airy-living-room-with-modern-decor-ZuHIek5xn_I
- https://unsplash.com/photos/modern-house-nestled-among-lush-green-tropical-trees-I7fSJgJh3w8
- https://unsplash.com/photos/a-modern-living-room-with-a-large-window-vIbxvHj9m9g
- https://unsplash.com/photos/modern-apartment-building-exterior-with-numerous-windows-and-balconies-lC2Atn-fmow
- https://unsplash.com/photos/modern-apartment-building-with-balconies-and-greenery-B9OMpxCdrlc
- https://unsplash.com/photos/a-lit-up-pool-and-house-at-night-4bW1uBe4KJc
- https://unsplash.com/photos/a-swimming-pool-outside-a-house-oQ7AV5nRxaI
- https://unsplash.com/photos/ocean-view-from-a-bedroom-with-a-balcony-YR9CSC9K9Wc
