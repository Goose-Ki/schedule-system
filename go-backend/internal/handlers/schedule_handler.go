package handlers

import (
	"strconv"

	"schedule-backend/internal/models"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func CreateScheduleItem(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var item models.ScheduleItem
		if err := c.ShouldBindJSON(&item); err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}

		if err := db.Create(&item).Error; err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}

		c.JSON(201, gin.H{"item": item, "message": "Schedule item created"})
	}
}

func GetSchedule(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID := c.Query("user_id")
		dayOfWeek := c.Query("day")

		var items []models.ScheduleItem
		query := db.Preload("User")

		if userID != "" {
			uid, _ := strconv.Atoi(userID)
			query = query.Where("user_id = ?", uid)
		}
		if dayOfWeek != "" {
			query = query.Where("day_of_week = ?", dayOfWeek)
		}

		if err := query.Order("time_start").Find(&items).Error; err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}

		c.JSON(200, gin.H{"items": items})
	}
}

func UpdateScheduleItem(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		id, err := strconv.Atoi(c.Param("id"))
		if err != nil {
			c.JSON(400, gin.H{"error": "Invalid ID"})
			return
		}

		var item models.ScheduleItem
		if err := db.First(&item, id).Error; err != nil {
			c.JSON(404, gin.H{"error": "Item not found"})
			return
		}

		if err := c.ShouldBindJSON(&item); err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}

		if err := db.Save(&item).Error; err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}

		c.JSON(200, gin.H{"item": item, "message": "Schedule item updated"})
	}
}

func DeleteScheduleItem(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		id, err := strconv.Atoi(c.Param("id"))
		if err != nil {
			c.JSON(400, gin.H{"error": "Invalid ID"})
			return
		}

		if err := db.Delete(&models.ScheduleItem{}, id).Error; err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}

		c.JSON(200, gin.H{"message": "Schedule item deleted"})
	}
}
