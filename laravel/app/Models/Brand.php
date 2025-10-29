<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Brand extends Model
{
    use HasFactory;

    protected $table = 'brands';
    public $timestamps = false;

    protected $fillable = [
        'name',
        'description',
        'logo_url',
    ];

    protected $casts = [
        'created_at' => 'datetime',
    ];

    // Relationships
    public function products()
    {
        return $this->hasMany(Product::class);
    }
}
