class GamificationService {
  constructor(databaseService) {
    this.db = databaseService;
    
    // XP rewards for different activities
    this.xpRewards = {
      'document_upload': 50,
      'chat_message': 5,
      'document_summary': 25,
      'quiz_generation': 30,
      'quiz_completion': 50,
      'perfect_quiz': 100,
      'daily_login': 10,
      'streak_3': 25,
      'streak_7': 50,
      'streak_14': 100,
      'streak_30': 250,
      'first_document': 75,
      'first_quiz': 75,
      'study_session': 20,
      'flashcard_study': 15,
      'voice_interaction': 10
    };

    // Achievement definitions
    this.achievements = {
      // Document-related achievements
      'first_upload': {
        title: 'First Steps',
        description: 'Uploaded your first document',
        xpReward: 50,
        icon: '📄',
        checkCondition: (stats) => stats.documents.total_documents >= 1
      },
      'document_collector': {
        title: 'Document Collector',
        description: 'Uploaded 10 documents',
        xpReward: 100,
        icon: '📚',
        checkCondition: (stats) => stats.documents.total_documents >= 10
      },
      'library_builder': {
        title: 'Library Builder',
        description: 'Uploaded 50 documents',
        xpReward: 250,
        icon: '🏛️',
        checkCondition: (stats) => stats.documents.total_documents >= 50
      },

      // Chat-related achievements
      'first_chat': {
        title: 'Breaking the Ice',
        description: 'Had your first chat with the AI',
        xpReward: 30,
        icon: '💬',
        checkCondition: (stats) => stats.chat.total_messages >= 1
      },
      'conversationalist': {
        title: 'Conversationalist',
        description: 'Sent 100 chat messages',
        xpReward: 150,
        icon: '🗣️',
        checkCondition: (stats) => stats.chat.total_messages >= 100
      },
      'chatter_expert': {
        title: 'Chat Expert',
        description: 'Completed 50 chat sessions',
        xpReward: 200,
        icon: '💭',
        checkCondition: (stats) => stats.chat.total_sessions >= 50
      },

      // Quiz-related achievements
      'quiz_rookie': {
        title: 'Quiz Rookie',
        description: 'Completed your first quiz',
        xpReward: 50,
        icon: '❓',
        checkCondition: (stats) => stats.quiz.completed_quizzes >= 1
      },
      'quiz_master': {
        title: 'Quiz Master',
        description: 'Completed 25 quizzes',
        xpReward: 200,
        icon: '🏆',
        checkCondition: (stats) => stats.quiz.completed_quizzes >= 25
      },
      'perfect_scorer': {
        title: 'Perfect Scorer',
        description: 'Achieved a perfect score on a quiz',
        xpReward: 100,
        icon: '⭐',
        checkCondition: (stats) => stats.quiz.average_score >= 100
      },
      'grade_a_student': {
        title: 'Grade A Student',
        description: 'Maintained an average score above 80%',
        xpReward: 150,
        icon: '🅰️',
        checkCondition: (stats) => stats.quiz.average_score >= 80
      },

      // Level-based achievements
      'level_up_5': {
        title: 'Rising Star',
        description: 'Reached level 5',
        xpReward: 100,
        icon: '🌟',
        checkCondition: (stats) => stats.user.level >= 5
      },
      'level_up_10': {
        title: 'Knowledge Seeker',
        description: 'Reached level 10',
        xpReward: 200,
        icon: '🔍',
        checkCondition: (stats) => stats.user.level >= 10
      },
      'level_up_20': {
        title: 'Learning Enthusiast',
        description: 'Reached level 20',
        xpReward: 500,
        icon: '🎓',
        checkCondition: (stats) => stats.user.level >= 20
      },

      // Streak achievements
      'streak_warrior': {
        title: 'Streak Warrior',
        description: 'Maintained a 7-day learning streak',
        xpReward: 100,
        icon: '🔥',
        checkCondition: async (stats, userId) => {
          const userService = require('./UserService');
          const streak = await userService.getUserStreak(userId);
          return streak.current >= 7;
        }
      },
      'consistency_king': {
        title: 'Consistency King',
        description: 'Maintained a 30-day learning streak',
        xpReward: 500,
        icon: '👑',
        checkCondition: async (stats, userId) => {
          const userService = require('./UserService');
          const streak = await userService.getUserStreak(userId);
          return streak.longest >= 30;
        }
      }
    };

    // Leaderboard categories
    this.leaderboardCategories = [
      'total_xp',
      'documents_uploaded',
      'quizzes_completed',
      'chat_messages',
      'current_level'
    ];
  }

  async addExperience(userId, points, activity, description = null) {
    try {
      console.log(`⭐ Adding ${points} XP to user ${userId} for ${activity}`);
      
      // Add XP transaction
      await this.db.addXPTransaction(userId, activity, points, description);
      
      // Update user's total XP and level
      const result = await this.db.updateUserXP(userId, points);
      
      // Check for new achievements
      const newAchievements = await this.checkAchievements(userId);
      
      // Check for level-up rewards
      const levelRewards = await this.checkLevelRewards(userId, result.levelUp, result.level);
      
      return {
        xpAdded: points,
        totalXP: result.xp,
        newLevel: result.level,
        levelUp: result.levelUp,
        newAchievements,
        levelRewards
      };
      
    } catch (error) {
      console.error('❌ Error adding experience:', error);
      throw error;
    }
  }

  async checkAchievements(userId) {
    try {
      const stats = await this.db.getUserStats(userId);
      const newAchievements = [];
      
      for (const [achievementId, achievement] of Object.entries(this.achievements)) {
        // Check if achievement already unlocked
        const existing = await this.db.get(
          'SELECT id FROM achievements WHERE user_id = ? AND achievement_type = ?',
          [userId, achievementId]
        );
        
        if (!existing) {
          // Check if condition is met
          let conditionMet = false;
          
          if (typeof achievement.checkCondition === 'function') {
            try {
              conditionMet = await achievement.checkCondition(stats, userId);
            } catch (error) {
              console.error(`Error checking achievement condition for ${achievementId}:`, error);
              conditionMet = false;
            }
          }
          
          if (conditionMet) {
            // Unlock achievement
            const achievementRecord = await this.db.addAchievement(
              userId,
              achievementId,
              achievement.title,
              achievement.description,
              achievement.xpReward
            );
            
            if (achievementRecord) {
              // Award XP for achievement
              await this.db.updateUserXP(userId, achievement.xpReward);
              
              newAchievements.push({
                id: achievementRecord,
                type: achievementId,
                title: achievement.title,
                description: achievement.description,
                xpReward: achievement.xpReward,
                icon: achievement.icon
              });
              
              console.log(`🏆 Achievement unlocked for user ${userId}: ${achievement.title}`);
            }
          }
        }
      }
      
      return newAchievements;
      
    } catch (error) {
      console.error('❌ Error checking achievements:', error);
      return [];
    }
  }

  async checkLevelRewards(userId, leveledUp, newLevel) {
    try {
      if (!leveledUp) return [];
      
      const rewards = [];
      
      // Level milestone rewards
      const milestones = {
        5: { xp: 50, title: 'Level 5 Bonus' },
        10: { xp: 100, title: 'Level 10 Bonus' },
        15: { xp: 150, title: 'Level 15 Bonus' },
        20: { xp: 200, title: 'Level 20 Bonus' },
        25: { xp: 250, title: 'Level 25 Bonus' },
        30: { xp: 300, title: 'Level 30 Bonus' }
      };
      
      if (milestones[newLevel]) {
        const milestone = milestones[newLevel];
        
        // Award milestone bonus
        await this.db.addXPTransaction(
          userId,
          'level_milestone',
          milestone.xp,
          milestone.title
        );
        
        rewards.push({
          type: 'milestone',
          title: milestone.title,
          xp: milestone.xp,
          level: newLevel
        });
        
        console.log(`🎯 Level milestone reward for user ${userId}: Level ${newLevel}`);
      }
      
      return rewards;
      
    } catch (error) {
      console.error('❌ Error checking level rewards:', error);
      return [];
    }
  }

  async getUserProgress(userId) {
    try {
      const stats = await this.db.getUserStats(userId);
      const achievements = await this.db.getUserAchievements(userId);
      const xpTransactions = await this.db.getUserXPTransactions(userId);
      
      // Calculate progress metrics
      const progress = {
        user: stats.user,
        level: {
          current: stats.user.level,
          xp: stats.user.xp,
          xpToNextLevel: this.calculateXPToNextLevel(stats.user.xp),
          progress: this.calculateLevelProgress(stats.user.xp)
        },
        activities: {
          documents: stats.documents,
          chat: stats.chat,
          quiz: stats.quiz
        },
        achievements: {
          total: achievements.length,
          recent: achievements.slice(0, 5),
          totalXPFromAchievements: achievements.reduce((sum, ach) => sum + ach.xp_reward, 0)
        },
        recentActivity: xpTransactions.slice(0, 10),
        streaks: await this.calculateStreaks(userId),
        badges: this.categorizeBadges(achievements),
        nextAchievements: await this.getNextAchievements(userId, stats)
      };
      
      return progress;
      
    } catch (error) {
      console.error('❌ Error getting user progress:', error);
      throw error;
    }
  }

  calculateXPToNextLevel(currentXP) {
    const currentLevel = Math.floor(currentXP / 100) + 1;
    const nextLevelXP = currentLevel * 100;
    return nextLevelXP - currentXP;
  }

  calculateLevelProgress(currentXP) {
    const currentLevel = Math.floor(currentXP / 100) + 1;
    const levelBaseXP = (currentLevel - 1) * 100;
    const levelXP = currentXP - levelBaseXP;
    return Math.round((levelXP / 100) * 100); // Percentage
  }

  async calculateStreaks(userId) {
    try {
      const transactions = await this.db.getUserXPTransactions(userId);
      
      if (transactions.length === 0) {
        return { current: 0, longest: 0, lastActivity: null };
      }
      
      // Group by date
      const activityDates = {};
      transactions.forEach(tx => {
        const date = new Date(tx.created_at).toDateString();
        activityDates[date] = true;
      });
      
      const dates = Object.keys(activityDates).sort((a, b) => new Date(a) - new Date(b));
      
      // Calculate current streak
      let currentStreak = 0;
      const today = new Date().toDateString();
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toDateString();
      
      if (dates.includes(today) || dates.includes(yesterday)) {
        let checkDate = new Date();
        while (dates.includes(checkDate.toDateString())) {
          currentStreak++;
          checkDate = new Date(checkDate.getTime() - 24 * 60 * 60 * 1000);
        }
      }
      
      // Calculate longest streak
      let longestStreak = 1;
      let tempStreak = 1;
      
      for (let i = 1; i < dates.length; i++) {
        const currentDate = new Date(dates[i]);
        const previousDate = new Date(dates[i - 1]);
        const dayDiff = (currentDate - previousDate) / (24 * 60 * 60 * 1000);
        
        if (dayDiff === 1) {
          tempStreak++;
          longestStreak = Math.max(longestStreak, tempStreak);
        } else {
          tempStreak = 1;
        }
      }
      
      return {
        current: currentStreak,
        longest: longestStreak,
        lastActivity: dates[dates.length - 1]
      };
      
    } catch (error) {
      console.error('❌ Error calculating streaks:', error);
      return { current: 0, longest: 0, lastActivity: null };
    }
  }

  categorizeBadges(achievements) {
    const categories = {
      documents: [],
      chat: [],
      quiz: [],
      level: [],
      streak: [],
      special: []
    };
    
    achievements.forEach(achievement => {
      const type = achievement.achievement_type;
      
      if (type.includes('upload') || type.includes('document')) {
        categories.documents.push(achievement);
      } else if (type.includes('chat') || type.includes('conversation')) {
        categories.chat.push(achievement);
      } else if (type.includes('quiz') || type.includes('score')) {
        categories.quiz.push(achievement);
      } else if (type.includes('level')) {
        categories.level.push(achievement);
      } else if (type.includes('streak')) {
        categories.streak.push(achievement);
      } else {
        categories.special.push(achievement);
      }
    });
    
    return categories;
  }

  async getNextAchievements(userId, stats) {
    try {
      const nextAchievements = [];
      
      // Check which achievements are closest to being unlocked
      for (const [achievementId, achievement] of Object.entries(this.achievements)) {
        const existing = await this.db.get(
          'SELECT id FROM achievements WHERE user_id = ? AND achievement_type = ?',
          [userId, achievementId]
        );
        
        if (!existing) {
          // Calculate progress towards this achievement
          let progress = 0;
          let total = 1;
          
          // Estimate progress based on achievement type
          if (achievementId.includes('document')) {
            if (achievementId === 'document_collector') {
              progress = stats.documents.total_documents;
              total = 10;
            } else if (achievementId === 'library_builder') {
              progress = stats.documents.total_documents;
              total = 50;
            }
          } else if (achievementId.includes('chat')) {
            if (achievementId === 'conversationalist') {
              progress = stats.chat.total_messages;
              total = 100;
            } else if (achievementId === 'chatter_expert') {
              progress = stats.chat.total_sessions;
              total = 50;
            }
          } else if (achievementId.includes('quiz')) {
            if (achievementId === 'quiz_master') {
              progress = stats.quiz.completed_quizzes;
              total = 25;
            }
          }
          
          if (progress > 0 && progress < total) {
            nextAchievements.push({
              id: achievementId,
              title: achievement.title,
              description: achievement.description,
              progress: progress,
              total: total,
              percentage: Math.round((progress / total) * 100),
              xpReward: achievement.xpReward,
              icon: achievement.icon
            });
          }
        }
      }
      
      // Sort by progress percentage (closest to completion first)
      return nextAchievements
        .sort((a, b) => b.percentage - a.percentage)
        .slice(0, 5);
      
    } catch (error) {
      console.error('❌ Error getting next achievements:', error);
      return [];
    }
  }

  async getUserAchievements(userId) {
    try {
      const achievements = await this.db.getUserAchievements(userId);
      
      return achievements.map(ach => ({
        id: ach.id,
        type: ach.achievement_type,
        title: ach.title,
        description: ach.description,
        xpReward: ach.xp_reward,
        unlockedAt: ach.unlocked_at,
        icon: this.achievements[ach.achievement_type]?.icon || '🏆'
      }));
      
    } catch (error) {
      console.error('❌ Error getting user achievements:', error);
      throw error;
    }
  }

  async getLeaderboard(category = 'total_xp', limit = 10) {
    try {
      let query = '';
      
      switch (category) {
        case 'total_xp':
          query = 'SELECT id, username, xp as score FROM users ORDER BY xp DESC LIMIT ?';
          break;
        case 'current_level':
          query = 'SELECT id, username, level as score FROM users ORDER BY level DESC, xp DESC LIMIT ?';
          break;
        case 'documents_uploaded':
          query = `SELECT u.id, u.username, COUNT(d.id) as score 
                   FROM users u 
                   LEFT JOIN documents d ON u.id = d.user_id 
                   GROUP BY u.id 
                   ORDER BY score DESC LIMIT ?`;
          break;
        case 'quizzes_completed':
          query = `SELECT u.id, u.username, COUNT(q.id) as score 
                   FROM users u 
                   LEFT JOIN quiz_sessions q ON u.id = q.user_id AND q.completed = 1 
                   GROUP BY u.id 
                   ORDER BY score DESC LIMIT ?`;
          break;
        case 'chat_messages':
          query = `SELECT u.id, u.username, COUNT(cm.id) as score 
                   FROM users u 
                   LEFT JOIN chat_sessions cs ON u.id = cs.user_id 
                   LEFT JOIN chat_messages cm ON cs.id = cm.session_id 
                   GROUP BY u.id 
                   ORDER BY score DESC LIMIT ?`;
          break;
        default:
          query = 'SELECT id, username, xp as score FROM users ORDER BY xp DESC LIMIT ?';
      }
      
      const results = await this.db.all(query, [limit]);
      
      return results.map((user, index) => ({
        rank: index + 1,
        userId: user.id,
        username: user.username,
        score: user.score || 0,
        category
      }));
      
    } catch (error) {
      console.error('❌ Error getting leaderboard:', error);
      return [];
    }
  }

  async getDailyChallenge(userId) {
    try {
      // Generate a daily challenge based on user's activity
      const stats = await this.db.getUserStats(userId);
      const today = new Date().toDateString();
      
      // Simple challenge generation based on user's least active area
      let challenge = {
        id: `daily_${today}`,
        title: 'Daily Learning Challenge',
        description: 'Complete your daily learning goal',
        xpReward: 25,
        progress: 0,
        target: 1,
        type: 'general'
      };
      
      if (stats.documents.total_documents < 5) {
        challenge = {
          id: `daily_upload_${today}`,
          title: 'Document Upload Challenge',
          description: 'Upload a new document to expand your knowledge base',
          xpReward: 50,
          progress: 0,
          target: 1,
          type: 'upload'
        };
      } else if (stats.chat.total_messages < 20) {
        challenge = {
          id: `daily_chat_${today}`,
          title: 'Chat Challenge',
          description: 'Have 5 conversations with your AI tutor',
          xpReward: 30,
          progress: 0,
          target: 5,
          type: 'chat'
        };
      } else if (stats.quiz.completed_quizzes < 5) {
        challenge = {
          id: `daily_quiz_${today}`,
          title: 'Quiz Challenge',
          description: 'Complete a quiz to test your knowledge',
          xpReward: 40,
          progress: 0,
          target: 1,
          type: 'quiz'
        };
      }
      
      return challenge;
      
    } catch (error) {
      console.error('❌ Error getting daily challenge:', error);
      return null;
    }
  }

  // Utility methods for XP calculations
  getXPForActivity(activity) {
    return this.xpRewards[activity] || 5;
  }

  calculateLevelFromXP(xp) {
    return Math.floor(xp / 100) + 1;
  }

  calculateXPForLevel(level) {
    return (level - 1) * 100;
  }

  async generateMotivationalMessage(userId) {
    try {
      const progress = await this.getUserProgress(userId);
      const messages = [];
      
      // Level-based messages
      if (progress.user.level < 5) {
        messages.push("You're off to a great start! Keep learning to unlock more features.");
      } else if (progress.user.level < 10) {
        messages.push("You're becoming a real knowledge seeker! Your dedication is showing.");
      } else {
        messages.push("Impressive! You're a true learning champion. Keep pushing the boundaries!");
      }
      
      // Achievement-based messages
      if (progress.achievements.total === 0) {
        messages.push("Your first achievement is just around the corner. Keep going!");
      } else if (progress.achievements.total < 5) {
        messages.push(`${progress.achievements.total} achievements unlocked! You're building an impressive collection.`);
      }
      
      // Streak-based messages
      if (progress.streaks.current > 0) {
        messages.push(`${progress.streaks.current} day learning streak! Consistency is key to success.`);
      }
      
      // Random motivational quotes
      const quotes = [
        "Learning never exhausts the mind. - Leonardo da Vinci",
        "The more you learn, the more you realize how much you don't know. - Albert Einstein",
        "Education is the most powerful weapon you can use to change the world. - Nelson Mandela",
        "Learning is a treasure that will follow its owner everywhere.",
        "The beautiful thing about learning is that no one can take it away from you."
      ];
      
      messages.push(quotes[Math.floor(Math.random() * quotes.length)]);
      
      return messages[Math.floor(Math.random() * messages.length)];
      
    } catch (error) {
      console.error('❌ Error generating motivational message:', error);
      return "Keep up the great work! Every step forward is progress.";
    }
  }
}

module.exports = GamificationService;