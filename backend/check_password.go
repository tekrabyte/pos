package main

import (
	"database/sql"
	"fmt"
	"log"
	
	_ "github.com/go-sql-driver/mysql"
	"golang.org/x/crypto/bcrypt"
)

func main() {
	dsn := "u215947863_pos_dev:Pos_dev123#@tcp(srv1412.hstgr.io:3306)/u215947863_pos_dev?parseTime=true&charset=utf8mb4"
	
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatalf("Failed to open database: %v", err)
	}
	defer db.Close()
	
	// Get user info
	var id int
	var username, password string
	err = db.QueryRow("SELECT id, username, password FROM users LIMIT 1").Scan(&id, &username, &password)
	if err != nil {
		log.Fatalf("Failed to get user: %v", err)
	}
	
	fmt.Printf("User ID: %d\n", id)
	fmt.Printf("Username: %s\n", username)
	fmt.Printf("Password hash: %s\n", password)
	fmt.Printf("Hash length: %d\n", len(password))
	
	// Test password
	testPassword := "admin123"
	err = bcrypt.CompareHashAndPassword([]byte(password), []byte(testPassword))
	if err == nil {
		fmt.Printf("\n✅ Password 'admin123' matches!\n")
	} else {
		fmt.Printf("\n❌ Password 'admin123' does NOT match: %v\n", err)
		
		// Generate new hash
		newHash, _ := bcrypt.GenerateFromPassword([]byte(testPassword), bcrypt.DefaultCost)
		fmt.Printf("\nNew hash for 'admin123': %s\n", string(newHash))
		
		// Update in database
		_, err = db.Exec("UPDATE users SET password = ? WHERE id = ?", string(newHash), id)
		if err != nil {
			fmt.Printf("Failed to update password: %v\n", err)
		} else {
			fmt.Printf("✅ Password updated in database!\n")
		}
	}
}
