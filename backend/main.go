package main

import (
	"fmt"
	"log"
	"os"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/joho/godotenv"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}

	// Initialize database
	if err := InitDatabase(); err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer CloseDatabase()

	// Create Fiber app
	app := fiber.New(fiber.Config{
		AppName: "Laravel POS API v1.0.0",
	})

	// Middleware
	app.Use(recover.New())
	
app.Use(cors.New(cors.Config{
		AllowOrigins: "*",
		AllowMethods: "GET,POST,PUT,DELETE,PATCH,OPTIONS",
		AllowHeaders: "*",
		AllowCredentials: true,
	}))
	app.Use(logger.New())

	// Routes
	SetupRoutes(app)

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8001"
	}

	log.Printf("Starting server on port %s", port)
	if err := app.Listen(fmt.Sprintf("0.0.0.0:%s", port)); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
