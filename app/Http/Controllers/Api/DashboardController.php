<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Product;
use App\Models\Customer;
use App\Models\OrderItem;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Carbon\Carbon;

class DashboardController extends Controller
{
    public function stats(Request $request)
    {
        $today = Carbon::today();
        $thisMonth = Carbon::now()->startOfMonth();
        
        // Today's stats
        $todayOrders = Order::whereDate('created_at', $today)->count();
        $todayRevenue = Order::whereDate('created_at', $today)
            ->where('status', 'completed')
            ->sum('total_amount');
        
        // This month stats
        $monthOrders = Order::where('created_at', '>=', $thisMonth)->count();
        $monthRevenue = Order::where('created_at', '>=', $thisMonth)
            ->where('status', 'completed')
            ->sum('total_amount');
        
        // All time stats
        $totalOrders = Order::count();
        $totalRevenue = Order::where('status', 'completed')->sum('total_amount');
        $totalCustomers = Customer::count();
        $totalProducts = Product::count();
        
        // Recent orders
        $recentOrders = Order::with(['customer', 'table', 'items'])
            ->orderBy('created_at', 'desc')
            ->limit(10)
            ->get();
        
        // Order status breakdown
        $ordersByStatus = Order::select('status', DB::raw('count(*) as count'))
            ->groupBy('status')
            ->get();
        
        // Top selling products
        $topProducts = OrderItem::select('product_id', 'product_name', DB::raw('SUM(quantity) as total_sold'))
            ->groupBy('product_id', 'product_name')
            ->orderBy('total_sold', 'desc')
            ->limit(10)
            ->get();
        
        // Revenue chart (last 7 days)
        $revenueChart = [];
        for ($i = 6; $i >= 0; $i--) {
            $date = Carbon::today()->subDays($i);
            $revenue = Order::whereDate('created_at', $date)
                ->where('status', 'completed')
                ->sum('total_amount');
            
            $revenueChart[] = [
                'date' => $date->format('Y-m-d'),
                'revenue' => (float) $revenue
            ];
        }
        
        return response()->json([
            'success' => true,
            'stats' => [
                'today' => [
                    'orders' => $todayOrders,
                    'revenue' => (float) $todayRevenue,
                ],
                'month' => [
                    'orders' => $monthOrders,
                    'revenue' => (float) $monthRevenue,
                ],
                'total' => [
                    'orders' => $totalOrders,
                    'revenue' => (float) $totalRevenue,
                    'customers' => $totalCustomers,
                    'products' => $totalProducts,
                ],
            ],
            'recent_orders' => $recentOrders,
            'orders_by_status' => $ordersByStatus,
            'top_products' => $topProducts,
            'revenue_chart' => $revenueChart,
        ]);
    }
    
    public function analytics(Request $request)
    {
        $startDate = $request->input('start_date', Carbon::now()->subDays(30));
        $endDate = $request->input('end_date', Carbon::now());
        
        // Revenue analytics
        $revenue = Order::whereBetween('created_at', [$startDate, $endDate])
            ->where('status', 'completed')
            ->sum('total_amount');
        
        // Order analytics
        $orderCount = Order::whereBetween('created_at', [$startDate, $endDate])->count();
        $averageOrderValue = $orderCount > 0 ? $revenue / $orderCount : 0;
        
        // Customer analytics
        $newCustomers = Customer::whereBetween('created_at', [$startDate, $endDate])->count();
        $returningCustomers = Order::whereBetween('created_at', [$startDate, $endDate])
            ->whereNotNull('customer_id')
            ->distinct('customer_id')
            ->count();
        
        // Product analytics
        $productsSold = OrderItem::whereHas('order', function($query) use ($startDate, $endDate) {
            $query->whereBetween('created_at', [$startDate, $endDate]);
        })->sum('quantity');
        
        // Best selling categories
        $topCategories = Product::select('categories.name', DB::raw('SUM(order_items.quantity) as total_sold'))
            ->join('order_items', 'products.id', '=', 'order_items.product_id')
            ->join('orders', 'order_items.order_id', '=', 'orders.id')
            ->join('categories', 'products.category_id', '=', 'categories.id')
            ->whereBetween('orders.created_at', [$startDate, $endDate])
            ->groupBy('categories.name')
            ->orderBy('total_sold', 'desc')
            ->limit(5)
            ->get();
        
        // Order type breakdown
        $orderTypes = Order::select('order_type', DB::raw('count(*) as count'))
            ->whereBetween('created_at', [$startDate, $endDate])
            ->groupBy('order_type')
            ->get();
        
        // Payment method breakdown
        $paymentMethods = Order::select('payment_method', DB::raw('count(*) as count'))
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
                'revenue' => (float) $revenue,
                'orders' => $orderCount,
                'average_order_value' => (float) $averageOrderValue,
                'new_customers' => $newCustomers,
                'returning_customers' => $returningCustomers,
                'products_sold' => $productsSold,
            ],
            'top_categories' => $topCategories,
            'order_types' => $orderTypes,
            'payment_methods' => $paymentMethods,
        ]);
    }
}
