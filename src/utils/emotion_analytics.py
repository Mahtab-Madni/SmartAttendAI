"""
Emotion & Engagement Analytics Service
Provides insights on student emotions and engagement levels
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

class EmotionAnalyticsService:
    """
    Analyzes emotional data from attendance records to provide teacher insights
    """
    
    # Emotion classifications
    POSITIVE_EMOTIONS = ['happy', 'confident', 'engaged', 'focused']
    NEGATIVE_EMOTIONS = ['bored', 'confused', 'sad', 'angry', 'frustrated']
    NEUTRAL_EMOTIONS = ['neutral', 'calm']
    
    def __init__(self, db):
        """Initialize with database reference"""
        self.db = db
    
    def generate_session_report(self, classroom: str, session_date: str) -> Dict:
        """
        Generate comprehensive post-lecture report with emotion insights
        """
        insights = self.db.get_classroom_insights(classroom, session_date)
        
        if not insights or not insights.get('emotions'):
            return {
                "status": "no_data",
                "message": "No emotion data available for this session"
            }
        
        emotion_percentages = insights.get('emotion_percentages', {})
        
        # Calculate engagement summary
        report = {
            "session_date": session_date,
            "classroom": classroom,
            "total_students": insights.get('total_students', 0),
            
            # Emotion breakdown
            "emotion_summary": {
                "positive": self._calculate_emotion_percentage(emotion_percentages, self.POSITIVE_EMOTIONS),
                "neutral": self._calculate_emotion_percentage(emotion_percentages, self.NEUTRAL_EMOTIONS),
                "negative": self._calculate_emotion_percentage(emotion_percentages, self.NEGATIVE_EMOTIONS),
            },
            
            # Detailed emotions
            "detailed_emotions": emotion_percentages,
            
            # Key insights
            "key_insights": self._generate_key_insights(insights, emotion_percentages),
            
            # Student concerns
            "students_needing_attention": insights.get('students_needing_attention', []),
            
            # Engagement score
            "average_engagement_score": insights.get('engagement_level', 0),
            
            # Recommendations
            "recommendations": self._generate_recommendations(
                emotion_percentages, 
                insights.get('students_needing_attention', [])
            )
        }
        
        return report
    
    def _calculate_emotion_percentage(self, emotion_percentages: Dict[str, float], 
                                     emotion_list: List[str]) -> float:
        """Calculate combined percentage for emotion category"""
        return round(
            sum(emotion_percentages.get(emotion, 0) for emotion in emotion_list),
            1
        )
    
    def _generate_key_insights(self, insights: Dict, emotion_percentages: Dict) -> List[str]:
        """Generate key insights based on emotion data"""
        insights_list = []
        total_students = insights.get('total_students', 0)
        
        if not emotion_percentages:
            return insights_list
        
        # Check for high confusion
        confusion_pct = emotion_percentages.get('confused', 0)
        if confusion_pct >= 30:
            confused_count = int(total_students * confusion_pct / 100)
            insights_list.append(
                f"⚠️ {confusion_pct}% of class ({confused_count} students) showed confusion during lecture"
            )
        
        # Check for boredom
        boredom_pct = emotion_percentages.get('bored', 0)
        if boredom_pct >= 25:
            bored_count = int(total_students * boredom_pct / 100)
            insights_list.append(
                f"📉 {boredom_pct}% of class ({bored_count} students) appeared bored or disengaged"
            )
        
        # Positive engagement
        positive_pct = sum(emotion_percentages.get(e, 0) for e in self.POSITIVE_EMOTIONS)
        if positive_pct >= 50:
            insights_list.append(
                f"✅ {positive_pct}% of students showed high engagement and focus"
            )
        
        # Engagement distribution
        if insights.get('average_engagement_score', 0) >= 0.8:
            insights_list.append(
                f"🎯 Class engagement score: {insights.get('average_engagement_score'):.0%} (Excellent)"
            )
        elif insights.get('average_engagement_score', 0) >= 0.6:
            insights_list.append(
                f"⚡ Class engagement score: {insights.get('average_engagement_score'):.0%} (Good)"
            )
        else:
            insights_list.append(
                f"📊 Class engagement score: {insights.get('average_engagement_score'):.0%} (Needs improvement)"
            )
        
        return insights_list
    
    def _generate_recommendations(self, emotion_percentages: Dict, 
                                 students_needing_attention: List) -> List[str]:
        """Generate actionable recommendations for teacher based on emotions"""
        recommendations = []
        
        # Based on confusion
        confusion_pct = emotion_percentages.get('confused', 0)
        if confusion_pct >= 30:
            recommendations.append(
                "💡 Consider revisiting the last section that caused confusion. "
                "Provide additional examples or visual aids."
            )
            recommendations.append(
                "🎓 Allocate more time for Q&A session to address student doubts"
            )
        
        # Based on boredom
        boredom_pct = emotion_percentages.get('bored', 0)
        if boredom_pct >= 25:
            recommendations.append(
                "🎨 Increase interactivity: Try more group discussions, activities, or real-world examples"
            )
            recommendations.append(
                "⏱️ Break monotony with varied teaching methods - mix lecture with activities"
            )
        
        # Based on negative emotions
        negative_total = sum(emotion_percentages.get(e, 0) for e in self.NEGATIVE_EMOTIONS)
        if negative_total >= 40:
            recommendations.append(
                "📢 Check in with low-engagement students individually to understand barriers"
            )
        
        # Based on students needing attention
        if students_needing_attention:
            recommendations.append(
                f"👥 Reach out to {len(students_needing_attention)} student(s) who appeared confused or disengaged"
            )
        
        # If no issues found
        if not recommendations:
            recommendations.append(
                "✨ Great session! Class was engaged and attentive throughout."
            )
        
        return recommendations
    
    def get_trend_analysis(self, classroom: str, days: int = 7) -> Dict:
        """
        Analyze emotion trends over multiple sessions
        """
        emotion_stats = self.db.get_emotion_statistics(
            classroom,
            (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d")
        )
        
        if not emotion_stats.get('emotions'):
            return {"status": "no_data"}
        
        return {
            "period_days": days,
            "classroom": classroom,
            "total_sessions": emotion_stats.get('total_records', 0),
            "emotion_distribution": emotion_stats.get('emotion_percentages', {}),
            "average_engagement": emotion_stats.get('average_engagement_score', 0),
            "dominant_emotion": emotion_stats.get('dominant_emotion'),
            "trend_summary": self._analyze_trend(emotion_stats.get('emotion_percentages', {}))
        }
    
    def _analyze_trend(self, emotion_percentages: Dict) -> str:
        """Analyze and describe the overall trend"""
        positive_pct = sum(emotion_percentages.get(e, 0) for e in self.POSITIVE_EMOTIONS)
        negative_pct = sum(emotion_percentages.get(e, 0) for e in self.NEGATIVE_EMOTIONS)
        
        if positive_pct > 60:
            return "🟢 Overall positive - Students are highly engaged"
        elif positive_pct > 40:
            return "🟡 Balanced engagement - Some areas for improvement"
        else:
            return "🔴 Low engagement - Significant intervention needed"
    
    def format_report_for_display(self, report: Dict) -> str:
        """Format report as readable teacher dashboard text"""
        if report.get('status') == 'no_data':
            return "No emotion data available for analysis."
        
        text = f"""
╔══════════════════════════════════════════════════════════════════╗
║           📊 POST-LECTURE ENGAGEMENT REPORT                      ║
╚══════════════════════════════════════════════════════════════════╝

Date: {report.get('session_date')}
Classroom: {report.get('classroom')}
Total Students: {report.get('total_students')}

─────────────────────────────────────────────────────────────────

📈 EMOTION DISTRIBUTION:
  ✅ Positive (Engaged):    {report.get('emotion_summary', {}).get('positive', 0)}%
  ⚪ Neutral (Calm):        {report.get('emotion_summary', {}).get('neutral', 0)}%
  ❌ Negative (Disengaged): {report.get('emotion_summary', {}).get('negative', 0)}%

─────────────────────────────────────────────────────────────────

💭 DETAILED EMOTIONS:
"""
        for emotion, percentage in report.get('detailed_emotions', {}).items():
            text += f"  • {emotion.capitalize()}: {percentage}%\n"
        
        text += f"\n🎯 ENGAGEMENT SCORE: {report.get('average_engagement_score', 0):.0%}\n\n"
        
        text += "─────────────────────────────────────────────────────────────────\n\n"
        
        text += "🔍 KEY INSIGHTS:\n"
        for insight in report.get('key_insights', []):
            text += f"  {insight}\n"
        
        if report.get('students_needing_attention'):
            text += f"\n⚠️  STUDENTS NEEDING ATTENTION ({len(report.get('students_needing_attention', []))}):\n"
            for student in report.get('students_needing_attention', [])[:5]:
                text += f"  • {student['name']} ({student['emotion']}) - Confidence: {student['confidence']}\n"
            if len(report.get('students_needing_attention', [])) > 5:
                text += f"  ... and {len(report.get('students_needing_attention', [])) - 5} more\n"
        
        text += "\n─────────────────────────────────────────────────────────────────\n\n"
        
        text += "💡 RECOMMENDATIONS:\n"
        for i, rec in enumerate(report.get('recommendations', []), 1):
            text += f"  {i}. {rec}\n"
        
        text += "\n" + "═" * 66 + "\n"
        
        return text

