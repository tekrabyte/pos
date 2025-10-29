<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Outlet extends Model
{
    use HasFactory;

    protected $table = 'outlets';
    public $timestamps = false;

    protected $fillable = [
        'name',
        'address',
        'city',
        'country',
        'postal_code',
        'is_main',
    ];

    protected $casts = [
        'is_main' => 'boolean',
        'created_at' => 'datetime',
    ];

    // Relationships
    public function users()
    {
        return $this->hasMany(User::class);
    }

    public function orders()
    {
        return $this->hasMany(Order::class);
    }
}
