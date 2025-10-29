<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class StoreSetting extends Model
{
    use HasFactory;

    protected $table = 'store_settings';
    const CREATED_AT = 'created_at';
    const UPDATED_AT = 'updated_at';

    protected $fillable = [
        'store_name',
        'store_description',
        'banner_url',
        'logo_url',
        'address',
        'phone',
        'email',
        'rating',
        'total_reviews',
        'opening_hours',
        'is_open',
    ];

    protected $casts = [
        'rating' => 'decimal:1',
        'total_reviews' => 'integer',
        'is_open' => 'boolean',
        'opening_hours' => 'array',
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
    ];
}
