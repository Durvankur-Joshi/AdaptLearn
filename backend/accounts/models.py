from django.db import models
from django.contrib.auth.models import User
import json

class LearningProfile(models.Model):
    """Student's learning profile and progress"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_profile')
    overall_theta = models.FloatField(default=0.0)  # IRT ability parameter
    current_subject = models.CharField(max_length=100, blank=True)
    current_concept = models.CharField(max_length=100, blank=True)
    learning_streak = models.IntegerField(default=0)
    total_time_spent = models.IntegerField(default=0)  # in minutes
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_profile'

class Concept(models.Model):
    """Learning concepts and atoms"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_concepts'
    )
    description = models.TextField(blank=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['subject', 'order']
        unique_together = ['name', 'subject', 'created_by']

class TeachingAtom(models.Model):
    """Atomic learning units"""
    PHASE_CHOICES = [
        ('not_started', 'Not Started'),
        ('diagnostic', 'Diagnostic'),
        ('teaching', 'Teaching'),
        ('practice', 'Practice'),
        ('reinforcement', 'Reinforcement'),
        ('mastery_check', 'Mastery Check'),
        ('complete', 'Complete'),
        ('fragile', 'Fragile'),
    ]
    
    name = models.CharField(max_length=200)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='atoms')
    explanation = models.TextField(blank=True)
    analogy = models.TextField(blank=True)
    examples = models.JSONField(default=list)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['concept', 'order']

class Question(models.Model):
    """Practice questions"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    COGNITIVE_CHOICES = [
        ('recall', 'Recall'),
        ('apply', 'Apply'),
        ('analyze', 'Analyze'),
    ]
    
    atom = models.ForeignKey(TeachingAtom, on_delete=models.CASCADE, related_name='questions')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    cognitive_operation = models.CharField(max_length=10, choices=COGNITIVE_CHOICES)
    estimated_time = models.IntegerField(default=60)  # in seconds
    question_text = models.TextField()
    options = models.JSONField(default=list)
    correct_index = models.IntegerField()
    
    def to_dict(self):
        return {
            'id': self.id,
            'difficulty': self.difficulty,
            'cognitive_operation': self.cognitive_operation,
            'estimated_time': self.estimated_time,
            'question': self.question_text,
            'options': self.options,
            'correct_index': self.correct_index,
        }

class StudentProgress(models.Model):
    """Track student progress on atoms — enriched for 10-feature pacing engine."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    atom = models.ForeignKey(TeachingAtom, on_delete=models.CASCADE)
    mastery_score = models.FloatField(default=0.0)
    phase = models.CharField(max_length=20, choices=TeachingAtom.PHASE_CHOICES, default='not_started')
    streak = models.IntegerField(default=0)
    hint_usage = models.IntegerField(default=0)
    error_history = models.JSONField(default=list)
    retention_verified = models.BooleanField(default=False)
    last_practiced = models.DateTimeField(auto_now=True)
    times_practiced = models.IntegerField(default=0)

    # ── Feature 2: per-atom learning speed ──
    time_per_question = models.JSONField(default=list, blank=True)  # list of floats (seconds)

    # ── Feature 6: retention tracking ──
    retention_score = models.FloatField(default=1.0)
    retention_checks_passed = models.IntegerField(default=0)
    retention_checks_failed = models.IntegerField(default=0)
    next_review_at = models.DateTimeField(null=True, blank=True)

    # ── Feature 10: velocity snapshots ──
    velocity_snapshots = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ['user', 'atom']


    
class KnowledgeLevel(models.TextChoices):
    ZERO = 'zero', 'Zero Knowledge'
    BEGINNER = 'beginner', 'Beginner'
    INTERMEDIATE = 'intermediate', 'Intermediate'
    ADVANCED = 'advanced', 'Advanced'


class LearningSession(models.Model):
    """Track learning sessions — enriched for 10-feature pacing engine."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_sessions')
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    questions_answered = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    hints_used = models.IntegerField(default=0)
    session_data = models.JSONField(default=dict)
    knowledge_level = models.CharField(
        max_length=20,
        choices=KnowledgeLevel.choices,
        default=KnowledgeLevel.ZERO
    )
    user_feedback = models.JSONField(default=dict)

    # ── Feature 8: fatigue tracking ──
    fatigue_level = models.CharField(max_length=20, default='fresh')   # fresh|mild|moderate|high|critical
    break_count = models.IntegerField(default=0)
    last_break_at = models.DateTimeField(null=True, blank=True)

    # ── Feature 9: engagement ──
    engagement_score = models.FloatField(default=0.7)
    consecutive_skips = models.IntegerField(default=0)

    # ── Feature 10: session-level velocity snapshots ──
    velocity_data = models.JSONField(default=list, blank=True)  


class UserXP(models.Model):
    """Track XP points for leaderboard"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='xp_profile')
    total_xp = models.IntegerField(default=0)
    questions_xp = models.IntegerField(default=0)
    atoms_xp = models.IntegerField(default=0)
    concepts_xp = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_xp'
        ordering = ['-total_xp']

    def __str__(self):
        return f"{self.user.username} - {self.total_xp} XP"

    def award_xp(self, amount, category='questions'):
        """Award XP and update totals"""
        self.total_xp += amount
        if category == 'questions':
            self.questions_xp += amount
        elif category == 'atoms':
            self.atoms_xp += amount
        elif category == 'concepts':
            self.concepts_xp += amount
        self.save()


# ==================== TEACHER MODELS ====================

class TeacherProfile(models.Model):
    """Teacher profile linked to a User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    subject = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)  # Requires admin approval
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teacher_profile'

    def __str__(self):
        return f"Teacher: {self.user.username} ({self.subject})"


class TeacherContent(models.Model):
    """Custom teaching content created by teachers for specific atoms"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_contents')
    atom = models.ForeignKey(TeachingAtom, on_delete=models.CASCADE, related_name='teacher_contents')
    explanation = models.TextField(blank=True, help_text='Custom explanation for the atom')
    analogy = models.TextField(blank=True, help_text='Custom analogy')
    examples = models.JSONField(default=list, help_text='Custom examples')
    tips = models.TextField(blank=True, help_text='Teaching tips for students')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    priority = models.BooleanField(default=True, help_text='If true, shown before AI content')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teacher_content'
        unique_together = ['teacher', 'atom']
        ordering = ['-priority', '-updated_at']

    def __str__(self):
        return f"Content by {self.teacher.username} for {self.atom.name}"


class QuestionApproval(models.Model):
    """Track teacher approval/rejection of AI-generated questions"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('edited', 'Edited & Approved'),
        ('disabled', 'Disabled'),
    ]

    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='approval')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='question_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, help_text='Teacher feedback on the question')
    edited_question_text = models.TextField(blank=True)
    edited_options = models.JSONField(default=list, blank=True)
    edited_correct_index = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'question_approval'
        ordering = ['-created_at']

    def __str__(self):
        return f"Q#{self.question.id} - {self.status}"


class TeacherOverride(models.Model):
    """Teacher interventions on student progress"""
    ACTION_CHOICES = [
        ('reset_mastery', 'Reset Mastery'),
        ('assign_atom', 'Assign Specific Atom'),
        ('force_review', 'Force Review'),
        ('set_mastery', 'Set Mastery Level'),
        ('assign_remedial', 'Assign Remedial Content'),
        ('skip_atom', 'Skip Atom'),
    ]

    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_overrides')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_overrides')
    atom = models.ForeignKey(TeachingAtom, on_delete=models.CASCADE, related_name='overrides', null=True, blank=True)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='overrides', null=True, blank=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    parameters = models.JSONField(default=dict, help_text='Action parameters (e.g., mastery value)')
    reason = models.TextField(blank=True, help_text='Why the teacher is intervening')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teacher_override'
        ordering = ['-created_at']

    def __str__(self):
        return f"Override: {self.teacher.username} → {self.student.username} ({self.action})"


class TeacherGoal(models.Model):
    """Goals/deadlines set by teachers for students"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='set_goals')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_goals', null=True, blank=True)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='goals', null=True, blank=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    target_mastery = models.FloatField(default=0.8)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_class_wide = models.BooleanField(default=False, help_text='If true, applies to all students')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teacher_goal'
        ordering = ['-created_at']

    def __str__(self):
        target = 'All Students' if self.is_class_wide else self.student.username if self.student else 'N/A'
        return f"Goal: {self.title} → {target}"



# ==================== PARENT MODELS ====================

class ParentProfile(models.Model):
    """Parent profile linked to a User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    display_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'parent_profile'

    def __str__(self):
        return f"Parent: {self.user.username}"


class ParentChild(models.Model):
    """Links a parent to a child (student). invite_code is used once to link; then cleared."""
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parent_children')
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='linked_parents', null=True, blank=True)
    linked_at = models.DateTimeField(null=True, blank=True)
    invite_code = models.CharField(max_length=20, unique=True, null=True, blank=True)

    class Meta:
        db_table = 'parent_child'
        # (parent, child) unique when child is set; multiple pending (child=null) invites per parent allowed
        unique_together = [['parent', 'child']]

    def __str__(self):
        return f"ParentChild: {self.parent.username} -> {self.child.username if self.child else 'pending'}"
# ==================== AI STUDY PLANNER ====================

class StudyPlanner(models.Model):
    GOAL_CHOICES = [
        ('study', 'Regular Study'),
        ('exam', 'Exam Preparation'),
        ('other', 'Other'),
    ]

    DAY_OPTION_CHOICES = [
        ('mon_fri', 'Monday to Friday'),
        ('mon_sun', 'Monday to Sunday'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_planners')
    goal_type = models.CharField(max_length=20, choices=GOAL_CHOICES)
    day_option = models.CharField(max_length=20, choices=DAY_OPTION_CHOICES)
    free_hours_per_day = models.IntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    # Store generated timetable
    timetable = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']


class PlannerSubject(models.Model):
    planner = models.ForeignKey(StudyPlanner, on_delete=models.CASCADE, related_name='subjects')
    subject_name = models.CharField(max_length=200)
    priority = models.IntegerField(default=1)  # 1 = high, 2 = medium, 3 = low

class StudyPlanItem(models.Model):
    planner = models.ForeignKey(
        StudyPlanner,
        on_delete=models.CASCADE,
        related_name="items"
    )

    date = models.DateField()
    subject = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    hours = models.FloatField(default=1)

    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.subject} - {self.topic}"
