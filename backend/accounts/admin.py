from django.contrib import admin
from .models import (
    Concept, TeachingAtom, Question, StudentProgress,
    LearningSession, LearningProfile, UserXP,
    TeacherProfile, TeacherContent, QuestionApproval,
    TeacherOverride, TeacherGoal,
)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'is_active', 'created_at']
    list_filter = ['is_active', 'subject', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'subject']
    list_editable = ['is_active']
    actions = ['approve_teachers', 'reject_teachers']
    ordering = ['-created_at']

    def approve_teachers(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} teacher(s) approved successfully.')
    approve_teachers.short_description = '✅ Approve selected teachers'

    def reject_teachers(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} teacher(s) rejected.')
    reject_teachers.short_description = '❌ Reject selected teachers'


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'difficulty', 'order']
    list_filter = ['subject', 'difficulty']
    search_fields = ['name', 'subject']


@admin.register(TeachingAtom)
class TeachingAtomAdmin(admin.ModelAdmin):
    list_display = ['name', 'concept', 'order']
    list_filter = ['concept__subject']
    search_fields = ['name', 'concept__name']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'atom', 'difficulty', 'cognitive_operation']
    list_filter = ['difficulty', 'cognitive_operation']
    search_fields = ['question_text']


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'atom', 'mastery_score', 'phase', 'streak']
    list_filter = ['phase']
    search_fields = ['user__username', 'atom__name']


@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'concept', 'start_time', 'questions_answered', 'correct_answers']
    list_filter = ['fatigue_level']
    search_fields = ['user__username', 'concept__name']


admin.site.register(LearningProfile)
admin.site.register(UserXP)
admin.site.register(TeacherContent)
admin.site.register(QuestionApproval)
admin.site.register(TeacherOverride)
admin.site.register(TeacherGoal)
