<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Order extends Model
{
    use HasFactory;

    protected $table = 'orders';
    public $timestamps = false;

    protected $fillable = [
        'order_number',
        'customer_id',
        'table_id',
        'order_type',
        'customer_name',
        'customer_phone',
        'outlet_id',
        'user_id',
        'total_amount',
        'payment_method',
        'payment_proof',
        'payment_verified',
        'status',
        'coupon_id',
        'coupon_code',
        'discount_amount',
        'original_amount',
        'estimated_time',
        'completed_at',
    ];

    protected $casts = [
        'total_amount' => 'decimal:2',
        'discount_amount' => 'decimal:2',
        'original_amount' => 'decimal:2',
        'payment_verified' => 'boolean',
        'estimated_time' => 'integer',
        'created_at' => 'datetime',
        'completed_at' => 'datetime',
    ];

    // Relationships
    public function customer()
    {
        return $this->belongsTo(Customer::class);
    }

    public function table()
    {
        return $this->belongsTo(Table::class);
    }

    public function outlet()
    {
        return $this->belongsTo(Outlet::class);
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function coupon()
    {
        return $this->belongsTo(Coupon::class);
    }

    public function items()
    {
        return $this->hasMany(OrderItem::class);
    }

    public function rating()
    {
        return $this->hasOne(OrderRating::class);
    }
}
