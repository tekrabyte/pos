# Laravel POS System Migration

## 🚀 Quick Start

### Prerequisites
- PHP 8.2+
- Composer
- MySQL Database (already configured)

### Installation
```bash
cd /app/laravel
composer install
```

### Configuration
Database sudah dikonfigurasi di `.env`:
- Host: srv1412.hstgr.io
- Database: u215947863_pos_dev
- Using existing production database

### Run Application
```bash
# Start Laravel server
php artisan serve --host=0.0.0.0 --port=8002

# Or use startup script
./start.sh
```

### Test API
```bash
# Health check
curl http://localhost:8002/api/health

# Staff login (credentials: admin/admin123)
curl -X POST http://localhost:8002/api/auth/staff/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 📋 Current Status

### ✅ Completed (30%)
- Laravel 11 setup
- JWT authentication
- 17 Eloquent Models
- Staff & Customer auth
- 3 CRUD controllers (Product, Category, Brand)

### ⏳ In Progress (70% remaining)
- 12 more API controllers
- Blade frontend (all pages)
- Services & utilities
- Testing & deployment

## 📚 Full Documentation
See [LARAVEL_MIGRATION_REPORT.md](../LARAVEL_MIGRATION_REPORT.md) for complete migration details.

## 🔑 Default Credentials

### Staff Login
- Username: `admin`
- Password: `admin123`

### Database
- All existing data from FastAPI is accessible
- No data migration needed

## 🏗️ Architecture

```
FastAPI (Port 8001) ─────┐
                         ├──→ MySQL Database
Laravel (Port 8002) ─────┘

React Frontend (Port 3000) → Can connect to either backend
```

## 📞 API Endpoints (Current)

### Authentication
- `POST /api/auth/staff/login` - Staff login
- `POST /api/auth/customer/login` - Customer login
- `POST /api/auth/customer/register` - Customer registration

### Products
- `GET /api/products` - List products
- `POST /api/products` - Create product
- `GET /api/products/{id}` - Get product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

### Categories
- `GET /api/categories` - List categories
- `POST /api/categories` - Create category
- `PUT /api/categories/{id}` - Update category
- `DELETE /api/categories/{id}` - Delete category

### Brands
- `GET /api/brands` - List brands
- `POST /api/brands` - Create brand
- `PUT /api/brands/{id}` - Update brand
- `DELETE /api/brands/{id}` - Delete brand

## 🔧 Development

### Clear Cache
```bash
php artisan config:clear
php artisan route:clear
php artisan view:clear
```

### Database Testing
```bash
php artisan tinker
>>> App\Models\User::count()
>>> App\Models\Product::with('category')->first()
```

## 📝 Notes

- Laravel menggunakan database yang SAMA dengan FastAPI
- Both systems can run bersamaan tanpa conflict
- JWT tokens berbeda antara FastAPI dan Laravel
- Migration in progress - see full report for details

---

**Last Updated:** 2025-01-29
**Version:** 1.0 Alpha
**Status:** Foundation Complete (30%)

---

## About Laravel

Laravel is a web application framework with expressive, elegant syntax. We believe development must be an enjoyable and creative experience to be truly fulfilling. Laravel takes the pain out of development by easing common tasks used in many web projects, such as:

- [Simple, fast routing engine](https://laravel.com/docs/routing).
- [Powerful dependency injection container](https://laravel.com/docs/container).
- Multiple back-ends for [session](https://laravel.com/docs/session) and [cache](https://laravel.com/docs/cache) storage.
- Expressive, intuitive [database ORM](https://laravel.com/docs/eloquent).
- Database agnostic [schema migrations](https://laravel.com/docs/migrations).
- [Robust background job processing](https://laravel.com/docs/queues).
- [Real-time event broadcasting](https://laravel.com/docs/broadcasting).

Laravel is accessible, powerful, and provides tools required for large, robust applications.

## Learning Laravel

Laravel has the most extensive and thorough [documentation](https://laravel.com/docs) and video tutorial library of all modern web application frameworks, making it a breeze to get started with the framework. You can also check out [Laravel Learn](https://laravel.com/learn), where you will be guided through building a modern Laravel application.

If you don't feel like reading, [Laracasts](https://laracasts.com) can help. Laracasts contains thousands of video tutorials on a range of topics including Laravel, modern PHP, unit testing, and JavaScript. Boost your skills by digging into our comprehensive video library.

## Laravel Sponsors

We would like to extend our thanks to the following sponsors for funding Laravel development. If you are interested in becoming a sponsor, please visit the [Laravel Partners program](https://partners.laravel.com).

### Premium Partners

- **[Vehikl](https://vehikl.com)**
- **[Tighten Co.](https://tighten.co)**
- **[Kirschbaum Development Group](https://kirschbaumdevelopment.com)**
- **[64 Robots](https://64robots.com)**
- **[Curotec](https://www.curotec.com/services/technologies/laravel)**
- **[DevSquad](https://devsquad.com/hire-laravel-developers)**
- **[Redberry](https://redberry.international/laravel-development)**
- **[Active Logic](https://activelogic.com)**

## Contributing

Thank you for considering contributing to the Laravel framework! The contribution guide can be found in the [Laravel documentation](https://laravel.com/docs/contributions).

## Code of Conduct

In order to ensure that the Laravel community is welcoming to all, please review and abide by the [Code of Conduct](https://laravel.com/docs/contributions#code-of-conduct).

## Security Vulnerabilities

If you discover a security vulnerability within Laravel, please send an e-mail to Taylor Otwell via [taylor@laravel.com](mailto:taylor@laravel.com). All security vulnerabilities will be promptly addressed.

## License

The Laravel framework is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).
