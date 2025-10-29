#!/usr/bin/env python3
"""
Laravel POS API Performance Comparison Test
Compares current response times with previous test results
"""

import requests
import json
import time
from datetime import datetime

class PerformanceComparisonTester:
    def __init__(self):
        self.api_url = "https://just-run-1.preview.emergentagent.com/api"
        self.token = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Previous test results from test_result.md
        self.previous_results = {
            'dashboard_stats': 10.207,  # was 10.207s - CRITICAL
            'analytics': 4.583,         # was 4.583s
            'products': 2.610,          # was 2.610s
            'orders': 3.254,            # was 3.254s
            'staff_login': 1.793,       # was 1.793s
            'categories': 1.972,        # was 1.972s
            'brands': 1.528,            # was 1.528s
            'tables': 1.551,            # was 1.551s
            'customers': 1.509,         # was 1.509s
            'coupons': 1.512,           # was 1.512s
            'outlets': 1.515,           # was 1.515s
            'payment_methods': 1.552    # was 1.552s
        }
        
        self.current_results = {}
        
    def make_request(self, method, endpoint, data=None, use_auth=False):
        """Make HTTP request with timing"""
        url = f"{self.api_url}{endpoint}"
        headers = self.headers.copy()
        
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=15)
            
            response_time = time.time() - start_time
            return response, response_time
            
        except requests.exceptions.RequestException as e:
            return None, 0
    
    def login(self):
        """Login and measure response time"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response, response_time = self.make_request('POST', '/auth/staff/login', login_data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.token = data['token']
                    self.current_results['staff_login'] = response_time
                    return True
            except json.JSONDecodeError:
                pass
        
        return False
    
    def test_endpoint(self, name, endpoint, use_auth=False):
        """Test a single endpoint and measure response time"""
        response, response_time = self.make_request('GET', endpoint, use_auth=use_auth)
        
        if response and response.status_code == 200:
            self.current_results[name] = response_time
            return True, response_time
        
        return False, 0
    
    def run_performance_tests(self):
        """Run all performance tests"""
        print("=" * 80)
        print("LARAVEL POS API PERFORMANCE COMPARISON TEST")
        print("=" * 80)
        print()
        
        # Login first
        print("🔐 Authenticating...")
        if not self.login():
            print("❌ Authentication failed - cannot proceed")
            return
        
        print(f"✅ Login completed in {self.current_results['staff_login']:.3f}s")
        print()
        
        # Test all endpoints
        endpoints = [
            ('products', '/products'),
            ('categories', '/categories'),
            ('brands', '/brands'),
            ('orders', '/orders'),
            ('tables', '/tables'),
            ('dashboard_stats', '/dashboard/stats'),
            ('analytics', '/analytics'),
            ('customers', '/customers'),
            ('coupons', '/coupons'),
            ('outlets', '/outlets'),
            ('payment_methods', '/payment-methods'),
        ]
        
        print("🚀 Testing API endpoints...")
        print("-" * 80)
        
        for name, endpoint in endpoints:
            success, response_time = self.test_endpoint(name, endpoint)
            
            if success:
                previous_time = self.previous_results.get(name, 0)
                improvement = previous_time - response_time
                improvement_pct = (improvement / previous_time * 100) if previous_time > 0 else 0
                
                status = "🚀" if improvement > 0 else "⚠️" if improvement < -0.5 else "✅"
                
                print(f"{status} {name.replace('_', ' ').title()}: {response_time:.3f}s "
                      f"(was {previous_time:.3f}s, {improvement:+.3f}s, {improvement_pct:+.1f}%)")
            else:
                print(f"❌ {name.replace('_', ' ').title()}: FAILED")
        
        print()
        self.analyze_performance()
    
    def analyze_performance(self):
        """Analyze performance improvements"""
        print("=" * 80)
        print("PERFORMANCE ANALYSIS")
        print("=" * 80)
        
        # Calculate overall statistics
        current_times = [t for t in self.current_results.values()]
        previous_times = [self.previous_results.get(k, 0) for k in self.current_results.keys()]
        
        current_avg = sum(current_times) / len(current_times)
        previous_avg = sum(previous_times) / len(previous_times)
        
        current_max = max(current_times)
        previous_max = max(previous_times)
        
        print(f"📊 OVERALL STATISTICS:")
        print(f"   Average Response Time: {current_avg:.3f}s (was {previous_avg:.3f}s)")
        print(f"   Maximum Response Time: {current_max:.3f}s (was {previous_max:.3f}s)")
        print(f"   Total Endpoints Tested: {len(current_times)}")
        print()
        
        # Success criteria analysis
        print(f"🎯 SUCCESS CRITERIA ANALYSIS:")
        
        # Dashboard stats < 3 seconds (was 10.2s)
        dashboard_time = self.current_results.get('dashboard_stats', 0)
        dashboard_target = dashboard_time < 3.0
        print(f"   Dashboard Stats < 3s: {'✅ PASS' if dashboard_target else '❌ FAIL'} "
              f"({dashboard_time:.3f}s, was 10.207s)")
        
        # Analytics < 2 seconds (was 4.6s)
        analytics_time = self.current_results.get('analytics', 0)
        analytics_target = analytics_time < 2.0
        print(f"   Analytics < 2s: {'✅ PASS' if analytics_target else '❌ FAIL'} "
              f"({analytics_time:.3f}s, was 4.583s)")
        
        # Products < 1 second (was 2.6s)
        products_time = self.current_results.get('products', 0)
        products_target = products_time < 1.0
        print(f"   Products < 1s: {'✅ PASS' if products_target else '❌ FAIL'} "
              f"({products_time:.3f}s, was 2.610s)")
        
        # Average < 1.5 seconds
        avg_target = current_avg < 1.5
        print(f"   Average < 1.5s: {'✅ PASS' if avg_target else '❌ FAIL'} "
              f"({current_avg:.3f}s)")
        
        print()
        
        # Biggest improvements
        improvements = []
        for name in self.current_results:
            if name in self.previous_results:
                current = self.current_results[name]
                previous = self.previous_results[name]
                improvement = previous - current
                improvement_pct = (improvement / previous * 100) if previous > 0 else 0
                improvements.append((name, improvement, improvement_pct, current, previous))
        
        improvements.sort(key=lambda x: x[1], reverse=True)
        
        print(f"🏆 BIGGEST IMPROVEMENTS:")
        for i, (name, improvement, improvement_pct, current, previous) in enumerate(improvements[:5]):
            if improvement > 0:
                print(f"   {i+1}. {name.replace('_', ' ').title()}: "
                      f"{improvement:.3f}s faster ({improvement_pct:.1f}% improvement)")
        
        print()
        
        # Performance concerns
        slow_endpoints = [(name, time) for name, time in self.current_results.items() if time > 2.0]
        if slow_endpoints:
            print(f"⚠️  PERFORMANCE CONCERNS (>2s):")
            for name, time in sorted(slow_endpoints, key=lambda x: x[1], reverse=True):
                print(f"   • {name.replace('_', ' ').title()}: {time:.3f}s")
        else:
            print(f"🎉 ALL ENDPOINTS UNDER 2 SECONDS!")
        
        print()
        
        # Final assessment
        critical_targets_met = dashboard_target and analytics_target
        performance_targets_met = products_target and avg_target
        
        if critical_targets_met and performance_targets_met:
            print(f"🎉 OPTIMIZATION SUCCESS: All performance targets achieved!")
        elif critical_targets_met:
            print(f"✅ CRITICAL TARGETS MET: Dashboard and Analytics optimized successfully")
        else:
            print(f"⚠️  OPTIMIZATION NEEDED: Some critical targets not yet achieved")

def main():
    """Main test execution"""
    tester = PerformanceComparisonTester()
    tester.run_performance_tests()

if __name__ == "__main__":
    main()