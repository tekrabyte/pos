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
	defer rows.Close()
	
	fmt.Println("Users table structure:")
	for rows.Next() {
		var field, typ, null, key, defaultVal, extra sql.NullString
		rows.Scan(&field, &typ, &null, &key, &defaultVal, &extra)
		fmt.Printf("  %s: %s\n", field.String, typ.String)
	}
	
	// Check existing user
	var id int
	var name, username, password string
	err = db.QueryRow("SELECT id, name, username, password FROM users LIMIT 1").Scan(&id, &name, &username, &password)
	if err != nil {
		log.Fatalf("Failed to get user: %v", err)
	}
	
	fmt.Printf("\nExisting user:\n  ID: %d\n  Name: %s\n  Username: %s\n  Password hash: %s...\n", 
		id, name, username, password[:20])
}
