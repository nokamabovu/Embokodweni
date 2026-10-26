# Embokodweni Lifestyle website

Django website for Embokodweni Lifestyle, Cunningmore A, Mpumalanga.
"Where Lifestyle Meets Entertainment."

Pages: Home, About, What we offer, What's on, Gallery, Book & contact.
Everything the venue changes often is managed in the Django admin:

| Admin section | What it controls |
|---|---|
| Site contact info | Phone, WhatsApp (adds the floating WhatsApp button), email, trading hours, social links, map link |
| Events | Weekly line-up (tick *is weekly* + weekday) and once-off special events (set a date). Optional poster image and entry price |
| Gallery photos | Upload photos, captions, which 5 show on the home page, order |
| Bookings | Bookings from the website, each with a reference (EMB-0001). Select bookings and use **Confirm** or **Decline**. Confirmed bookings make that date show as fully booked |
| Blocked dates | Days the venue can't take bookings (private function, closed). They show as unavailable |
| Site contact info > Bookings | How many confirmed bookings a day can take, and the largest group size |

## Staff dashboard

How staff get in (no need to type the address):
- **Hidden entrance**: tap the logo in the website footer **3 times quickly** (or **press and hold** it for 1.5 seconds on a phone).
- **App icon**: on the login page, tap **Install on this phone** (Android/Chrome) or, on iPhone, Share > **Add to Home Screen**.
  The "Embo Staff" icon then opens the dashboard directly.
- **Floating button**: while logged in, a **Dashboard** button (with the number of new items) shows on every website page. Visitors never see it.
- The address **/dashboard/** still works too.

Security: only staff accounts can log in; after 5 wrong passwords that device is locked for 15 minutes;
"Keep me logged in" keeps the session for 30 days on that device, otherwise it ends when the browser closes.

- **Overview**: new and unread items, pending bookings, busy-date questions, the next 14 days and recent activity.
- **Inbox**: every booking, busy-date question and Contact-page message in one list, with filters and search.
  Open an item to confirm or decline it, call / WhatsApp / email the customer and keep private staff notes.
- **Notifications**: the bell updates every 30 seconds while the dashboard is open and pops up new bookings and messages.
- **Blocked dates**: block or unblock days on the website calendar.

Create a staff login for the owner:

```powershell
python manage.py createsuperuser
```

or, in **/admin/ > Users**, add a user and tick **Staff status**. Only staff users can open the dashboard.

## Run locally (Windows / PowerShell)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_site        # adds a sample weekly line-up (photos are built in)
python manage.py createsuperuser
python manage.py runserver
```

Site: http://127.0.0.1:8000  Admin: http://127.0.0.1:8000/admin

## Deploy on Render

1. Push to GitHub, then on Render choose **New > Blueprint** and pick the repo (uses `render.yaml`),
   or create a Web Service with build command `./build.sh` and start command `gunicorn config.wsgi:application`.
2. Environment variables: `DEBUG=False`, `SECRET_KEY` (generated), and for enquiry emails
   `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (Gmail app password), `ENQUIRY_NOTIFY_EMAIL`.
   For an Outlook / Microsoft 365 mailbox also set `EMAIL_HOST=smtp.office365.com`.
3. Custom domain: add it on Render and set `EXTRA_HOSTS=embokodweni.co.za,www.embokodweni.co.za`.

**Important about storage on Render's free plan:** the disk resets on every deploy/restart.
The seed command puts the starting photos and line-up back each time, but enquiries,
admin changes and uploaded photos made on the live site will be lost. Options:
- Paid plan with a disk: uncomment the `disk`, `SQLITE_PATH` and `MEDIA_ROOT` lines in `render.yaml`.
- Or make content changes locally and push `db.sqlite3` and `media/` with the repo
  (then remove `media/` from `.gitignore`). Enquiries still reach the team by email either way.

## Before launch, get from the client

- Phone, WhatsApp number, email, trading hours, social media links, Google Maps link
- The real weekly line-up (the seeded one is a sample)
- Photos of the venue itself: bar, braai area, DJ booth, screens, VIP area
- Domain name
