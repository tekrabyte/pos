package main

import (
	"database/sql"
	"fmt"
	"log"
	
	_ "github.com/go-sql-driver/mysql"
)

func main() {
	dsn := "u215947863_pos_dev:Pos_dev123#@tcp(srv1412.hstgr.io:3306)/u215947863_pos_dev?parseTime=true&charset=utf8mb4"
	
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatalf("Failed to open database: %v", err)
	}
	defer db.Close()
	
	if err := db.Ping(); err != nil {
		log.Fatalf("Failed to ping database: %v", err)
	}
	
	fmt.Println("✅ Database connection successful!")
	
	// List tables
	rows, err := db.Query("SHOW TABLES")
	if err != nil {
		log.Fatalf("Failed to list tables: %v", err)
	}
	defer rows.Close()
	
	fmt.Println("\nTables in database:")
	for rows.Next() {
		var table string
		rows.Scan(&table)
		fmt.Printf("  - %s\n", table)
	}
	
	// Check users table
	var count int
	err = db.QueryRow("SELECT COUNT(*) FROM users").Scan(&count)
	if err != nil {
		fmt.Printf("\n❌ Error checking users table: %v\n", err)
	} else {
		fmt.Printf("\nUsers in database: %d\n", count)
	}
}
