package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func GetScheduleByID(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		idStr := c.Param("id")
		id, err := strconv.Atoi(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Invalid schedule ID"})
			return
		}

		var scheduleItem struct {
			ID          int    `json:"id"`
			UserID      int    `json:"user_id"`
			DayOfWeek   string `json:"day_of_week"`
			TimeStart   string `json:"time_start"`
			TimeEnd     string `json:"time_end"`
			Subject     string `json:"subject"`
			Description string `json:"description"`
			CreatedAt   string `json:"created_at"`
		}

		result := db.Table("schedule_items").Where("id = ?", id).First(&scheduleItem)
		if result.Error != nil {
			if result.Error == gorm.ErrRecordNotFound {
				c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Schedule item not found"})
			} else {
				c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": result.Error.Error()})
			}
			return
		}

		c.JSON(http.StatusOK, gin.H{"success": true, "item": scheduleItem})
	}
}
