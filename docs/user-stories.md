# User Stories

## Roles (final)

### Worker — front line

### Supervisor — worker + oversight

### Manager — supervisor + pricing + buying

### Admin — everything + users/system

## Worker
As a worker, I want to log in, so that the system knows who recorded each sale.

As a worker, I want to record a sale, so that stock and revenue update automatically.

As a worker, I want to view orders, so that I can check what was sold and when.

As a worker, I want to view current stock levels, so that I can tell a customer if an item is available.

(That's it. Workers shouldn't touch prices, restocking decisions, or reports.)

## Supervisor
Everything a worker can do, plus:

As a supervisor, I want to view low-stock items, so that I can flag what needs restocking.

As a supervisor, I want to submit a restock request to the manager, so that purchasing gets triggered.

As a supervisor, I want to view sales reports, so that I can track daily/weekly performance.

As a supervisor, I want to see which worker recorded each sale, so that I can follow up on errors.

(You mentioned reports — I'd keep full analytics for Manager, and give Supervisor a lighter daily/weekly view. Otherwise the roles overlap.)

## Manager
Everything a supervisor can do, plus:

As a manager, I want to set and update prices, so that margins stay correct.

As a manager, I want to approve or reject restock requests, so that spending is controlled.

As a manager, I want to manage suppliers, so that I know who to order from.

As a manager, I want to set reorder levels per product, so that low-stock alerts are automatic.

As a manager, I want to view full sales and stock reports, so that I can plan purchases.

As a manager, I want to export reports, so that I can share them with owners.

As an manger, I want to create/deactivate user accounts, so that ex-staff can't log in.

As an manager, I want to assign roles, so that workers can't access manager features.

As an manager, I want to view system activity logs, so that I can audit changes.

