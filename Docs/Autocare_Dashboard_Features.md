# Digital AutoCare Dashboard — Primary Screen Features

## 1. Vehicle Overview Card
- **Display Elements:** Vehicle image, make, model, year, and VIN.
- **Live Status Indicators:** Engine health, oil life, tire pressure, battery level.
- **Quick Actions:** Remote lock/unlock, start engine, locate vehicle.

## 2. Upcoming Maintenance
- **Functionality:** Displays upcoming scheduled services such as oil change, tire rotation, or inspection.
- **Reminders:** Push notifications and email alerts before service dates.
- **Action Buttons:** “Book Service” or “Contact Mechanic.”

## 3. Maintenance History
- **Display Elements:** Timeline or list of completed services, dates, mileage, service center, and cost.
- **Document Upload:** Option to attach invoices, receipts, or reports.
- **Analytics:** Summary of total maintenance cost per year.

## 4. VIN Decoder
- **Functionality:** Auto-decodes VIN to display vehicle specifications.
- **Details Displayed:** Engine type, transmission, model year, trim, manufacturing plant, and safety features.
- **Integration:** Pulls data from VIN databases or APIs like NHTSA or Carfax.

## 5. Mechanic Services
- **Features:**
  - Search nearby mechanics or workshops.
  - View profiles with ratings, service types, and availability.
  - Book appointments directly.
- **Integration:** Google Maps API for location services.

## 6. Alerts and Notifications
- **Types of Alerts:**
  - Low fuel or oil levels.
  - Maintenance due soon.
  - Safety recalls or fault codes detected.
- **Design:** Card layout with color-coded severity (red for urgent, yellow for upcoming, green for normal).

## 7. Cost Analysis Chart
- **Display Elements:**
  - Interactive graph showing monthly or 6-month spending trends.
  - Filters for service categories (engine, tires, general, bodywork).
  - Comparison with average vehicle maintenance costs.
- **Technology:** Chart.js or Recharts integration.

## 8. Bookings and Appointments
- **Display:** List of upcoming bookings and their status (pending, confirmed, completed).
- **Actions:** Reschedule or cancel appointments.
- **Integration:** Sync with Google Calendar or internal notification system.

## 9. Alerts Feed / Deals Section
- **Purpose:** Display promotional offers from partner garages or service plans.
- **Design:** Card-based scrolling list with icons and short descriptions.

## 10. User Profile & Settings
- **Display:** User name, registered vehicles, and linked payment options.
- **Preferences:** Notification settings, app theme, and data sync options.
- **Account Management:** Manage connected vehicles and logout functionality.

---

### Visual Design Notes
- **Color Scheme:** Soft grey and white contrast for a clean, modern interface.
- **Typography:** Rounded sans-serif font for readability.
- **UI Elements:** Large rounded buttons, subtle shadows, and minimalistic icons.
- **Mobile First:** Fully responsive layout with key metrics prioritized for small screens.
