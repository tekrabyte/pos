<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Product;
use App\Models\Customer;
use App\Models\OrderItem;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Cache;
use Carbon\Carbon;

class DashboardController extends Controller
{
    public function stats(Request $request)
    {
        // Cache dashboard stats for 5 minutes
        return Cache::remember('dashboard_stats', 300, function () {
            $today = Carbon::today();
            $thisMonth = Carbon::now()->startOfMonth();
            
            // Use single query for today's stats
            $todayStats = DB::table('orders')
                ->selectRaw('COUNT(*) as order_count, SUM(CASE WHEN status = "completed" THEN total_amount ELSE 0 END) as revenue')
                ->whereDate('created_at', $today)
                ->first();
            
            // Use single query for month stats
            $monthStats = DB::table('orders')
                ->selectRaw('COUNT(*) as order_count, SUM(CASE WHEN status = "completed" THEN total_amount ELSE 0 END) as revenue')
                ->where('created_at', '>=', $thisMonth)
                ->first();
            
            // Use single query for total stats
            $totalStats = DB::table('orders')
                ->selectRaw('COUNT(*) as order_count, SUM(CASE WHEN status = "completed" THEN total_amount ELSE 0 END) as revenue')
                ->first();
            
            $totalCustomers = DB::table('customers')->count();
            $totalProducts = DB::table('products')->count();
            
            // Recent orders - optimized with specific columns
            $recentOrders = Order::select([
                'orders.id', 'orders.order_number', 'orders.total_amount', 
                'orders.status', 'orders.created_at', 'orders.customer_id', 'orders.table_id'
            ])
                ->with(['customer:id,name', 'table:id,table_number'])
                ->orderBy('created_at', 'desc')
                ->limit(10)
                ->get();
            
            // Order status breakdown
            $ordersByStatus = DB::table('orders')
                ->select('status', DB::raw('count(*) as count'))
                ->groupBy('status')
                ->get();
            
            // Top selling products - optimized
            $topProducts = DB::table('order_items')
                ->select('product_id', 'product_name', DB::raw('SUM(quantity) as total_sold'))
                ->groupBy('product_id', 'product_name')
                ->orderBy('total_sold', 'desc')
                ->limit(10)
                ->get();
            
            // Revenue chart (last 7 days) - single query
            $revenueChart = DB::table('orders')
                ->selectRaw('DATE(created_at) as date, SUM(CASE WHEN status = "completed" THEN total_amount ELSE 0 END) as revenue')
                ->where('created_at', '>=', Carbon::today()->subDays(6))
                ->groupBy('date')
                ->orderBy('date')
                ->get()
                ->map(function($item) {
                    return [
                        'date' => $item->date,
                        'revenue' => (float) $item->revenue
                    ];
                });
            
            return response()->json([
                'success' => true,
                'stats' => [
                    'today' => [
                        'orders' => $todayStats->order_count,
                        'revenue' => (float) $todayStats->revenue,
                    ],
                    'month' => [
                        'orders' => $monthStats->order_count,
                        'revenue' => (float) $monthStats->revenue,
                    ],
                    'total' => [
                        'orders' => $totalStats->order_count,
                        'revenue' => (float) $totalStats->revenue,
                        'customers' => $totalCustomers,
                        'products' => $totalProducts,
                    ],
                ],
                'recent_orders' => $recentOrders,
                'orders_by_status' => $ordersByStatus,
                'top_products' => $topProducts,
                'revenue_chart' => $revenueChart,
            ]);
        });
    }
    
    public function analytics(Request $request)
    {
        $startDate = $request->input('start_date', Carbon::now()->subDays(30)->toDateString());
        $endDate = $request->input('end_date', Carbon::now()->toDateString());
        
        // Cache analytics for 10 minutes per date range
        $cacheKey = "analytics_{$startDate}_{$endDate}";
        
        return Cache::remember($cacheKey, 600, function () use ($startDate, $endDate) {
            // Single optimized query for order analytics
            $orderStats = DB::table('orders')
                ->selectRaw('
                    COUNT(*) as order_count,
                    SUM(CASE WHEN status = "completed" THEN total_amount ELSE 0 END) as revenue,
                    COUNT(DISTINCT customer_id) as unique_customers
                ')
                ->whereBetween('created_at', [$startDate, $endDate])
                ->first();
            
            $averageOrderValue = $orderStats->order_count > 0 ? $orderStats->revenue / $orderStats->order_count : 0;
            
            // New customers count
            $newCustomers = DB::table('customers')
                ->whereBetween('created_at', [$startDate, $endDate])
                ->count();
            
            // Products sold - optimized
            $productsSold = DB::table('order_items')
                ->join('orders', 'order_items.order_id', '=', 'orders.id')
                ->whereBetween('orders.created_at', [$startDate, $endDate])
                ->sum('order_items.quantity');
            
            // Best selling categories - optimized with joins
            $topCategories = DB::table('categories')
                ->select('categories.name', DB::raw('SUM(order_items.quantity) as total_sold'))
                ->join('products', 'categories.id', '=', 'products.category_id')
                ->join('order_items', 'products.id', '=', 'order_items.product_id')
                ->join('orders', 'order_items.order_id', '=', 'orders.id')
                ->whereBetween('orders.created_at', [$startDate, $endDate])
                ->groupBy('categories.name')
                ->orderBy('total_sold', 'desc')
                ->limit(5)
                ->get();
            
            // Order type breakdown
            $orderTypes = DB::table('orders')
                ->select('order_type', DB::raw('count(*) as count'))
                ->whereBetween('created_at', [$startDate, $endDate])
                ->groupBy('order_type')
                ->get();
            
            // Payment method breakdown
            $paymentMethods = DB::table('orders')
                ->select('payment_method', DB::raw('count(*) as count'))
                ->whereBetween('created_at', [$startDate, $endDate])
                ->whereNotNull('payment_method')
                ->groupBy('payment_method')
                ->get();
            
            return response()->json([
                'success' => true,
                'period' => [
                    'start_date' => $startDate,
                    'end_date' => $endDate,
                ],
                'analytics' => [
                    'revenue' => (float) $orderStats->revenue,
                    'orders' => $orderStats->order_count,
                    'average_order_value' => (float) $averageOrderValue,
                    'new_customers' => $newCustomers,
                    'returning_customers' => $orderStats->unique_customers,
                    'products_sold' => $productsSold,
                ],
                'top_categories' => $topCategories,
                'order_types' => $orderTypes,
                'payment_methods' => $paymentMethods,
            ]);
        });
    }
}
