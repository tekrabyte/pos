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
	
	// Describe users table
	rows, err := db.Query("DESCRIBE users")
	if err != nil {
		log.Fatalf("Failed to describe users table: %v", err)
	}
	
	fmt.Println("Users table structure:")
	for rows.Next() {
		var field, typ, null, key, defaultVal, extra sql.NullString
		rows.Scan(&field, &typ, &null, &key, &defaultVal, &extra)
		fmt.Printf("  %s: %s (Null: %s, Key: %s)\n", field.String, typ.String, null.String, key.String)
	}
	rows.Close()
	
	// Select all columns from users
	rows2, err := db.Query("SELECT * FROM users LIMIT 1")
	if err != nil {
		log.Fatalf("Failed to query users: %v", err)
	}
	defer rows2.Close()
	
	cols, _ := rows2.Columns()
	fmt.Printf("\nActual columns returned by SELECT *: %v\n", cols)
}
