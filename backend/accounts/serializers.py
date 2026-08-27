from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # Create learning profile for the user
        from .models import LearningProfile
        LearningProfile.objects.create(user=user)
        
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        
        
        
from .models import (
    LearningProfile, Concept, TeachingAtom, 
    Question, StudentProgress, LearningSession,
    TeacherProfile, TeacherContent, QuestionApproval,
    TeacherOverride, TeacherGoal,
    ParentProfile, ParentChild,
)

class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ['id', 'name', 'subject', 'description', 'difficulty', 'order']

class TeachingAtomSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingAtom
        fields = ['id', 'name', 'explanation', 'analogy', 'examples', 'order']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'difficulty', 'cognitive_operation', 'estimated_time', 
                 'question_text', 'options', 'correct_index']

class StudentProgressSerializer(serializers.ModelSerializer):
    atom_name = serializers.CharField(source='atom.name', read_only=True)
    atom_id = serializers.IntegerField(source='atom.id', read_only=True)
    concept_name = serializers.CharField(source='atom.concept.name', read_only=True)
    concept_id = serializers.IntegerField(source='atom.concept.id', read_only=True)
    subject = serializers.CharField(source='atom.concept.subject', read_only=True)
    
    class Meta:
        model = StudentProgress
        fields = ['id', 'atom_id', 'atom_name', 'concept_id', 'concept_name', 'subject',
                 'mastery_score', 'phase', 'streak', 'hint_usage', 'retention_verified']

class LearningSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningSession
        fields = ['id', 'concept', 'start_time', 'end_time', 'questions_answered',
                 'correct_answers', 'hints_used']


# ==================== TEACHER SERIALIZERS ====================

class TeacherProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'subject', 'bio', 'is_active', 'created_at']


class TeacherRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    subject = serializers.CharField(max_length=200, required=False, default='')
    bio = serializers.CharField(required=False, default='')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        from django.contrib.auth.models import User
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists."})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        return attrs

    def create(self, validated_data):
        from django.contrib.auth.models import User
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_staff=True,  # Teachers get staff status
        )
        TeacherProfile.objects.create(
            user=user,
            subject=validated_data.get('subject', ''),
            bio=validated_data.get('bio', ''),
        )
        return user


class TeacherContentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    atom_name = serializers.CharField(source='atom.name', read_only=True)
    concept_name = serializers.CharField(source='atom.concept.name', read_only=True)

    class Meta:
        model = TeacherContent
        fields = ['id', 'teacher', 'teacher_name', 'atom', 'atom_name', 'concept_name',
                  'explanation', 'analogy', 'examples', 'tips', 'status', 'priority',
                  'created_at', 'updated_at']
        read_only_fields = ['teacher', 'created_at', 'updated_at']


class QuestionApprovalSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    question_options = serializers.JSONField(source='question.options', read_only=True)
    question_correct_index = serializers.IntegerField(source='question.correct_index', read_only=True)
    question_difficulty = serializers.CharField(source='question.difficulty', read_only=True)
    atom_name = serializers.CharField(source='question.atom.name', read_only=True)
    concept_name = serializers.CharField(source='question.atom.concept.name', read_only=True)

    class Meta:
        model = QuestionApproval
        fields = ['id', 'question', 'question_text', 'question_options', 'question_correct_index',
                  'question_difficulty', 'atom_name', 'concept_name', 'teacher', 'status',
                  'feedback', 'edited_question_text', 'edited_options', 'edited_correct_index',
                  'reviewed_at', 'created_at']
        read_only_fields = ['teacher', 'created_at', 'reviewed_at']


class TeacherOverrideSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    atom_name = serializers.CharField(source='atom.name', read_only=True, default=None)
    concept_name = serializers.CharField(source='concept.name', read_only=True, default=None)

    class Meta:
        model = TeacherOverride
        fields = ['id', 'teacher', 'teacher_name', 'student', 'student_name', 'student_username',
                  'atom', 'atom_name', 'concept', 'concept_name', 'action', 'parameters',
                  'reason', 'is_active', 'created_at']
        read_only_fields = ['teacher', 'created_at']


class TeacherGoalSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    student_name = serializers.SerializerMethodField()
    concept_name = serializers.CharField(source='concept.name', read_only=True, default=None)

    class Meta:
        model = TeacherGoal
        fields = ['id', 'teacher', 'teacher_name', 'student', 'student_name',
                  'concept', 'concept_name', 'title', 'description', 'deadline',
                  'target_mastery', 'status', 'is_class_wide', 'created_at']
        read_only_fields = ['teacher', 'created_at']

    def get_student_name(self, obj):
        if obj.is_class_wide:
            return 'All Students'
        return obj.student.get_full_name() if obj.student else None


class StudentDetailSerializer(serializers.ModelSerializer):
    """Detailed student info for teacher dashboard"""
    progress = serializers.SerializerMethodField()
    total_xp = serializers.SerializerMethodField()
    weak_areas = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email',
                  'progress', 'total_xp', 'weak_areas']

    def get_progress(self, obj):
        progresses = StudentProgress.objects.filter(user=obj).select_related('atom__concept')
        return StudentProgressSerializer(progresses, many=True).data

    def get_total_xp(self, obj):
        try:
            return obj.xp_profile.total_xp
        except Exception:
            return 0

    def get_weak_areas(self, obj):
        weak = StudentProgress.objects.filter(
            user=obj, mastery_score__lt=0.5
        ).select_related('atom__concept').order_by('mastery_score')[:10]
        return [{
            'atom_id': p.atom.id,
            'atom_name': p.atom.name,
            'concept_name': p.atom.concept.name,
            'mastery_score': p.mastery_score,
            'phase': p.phase,
        } for p in weak]
        
        

# ==================== PARENT SERIALIZERS ====================

class ParentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = ParentProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'display_name', 'is_active', 'created_at']


class ParentRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    display_name = serializers.CharField(max_length=200, required=False, default='')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists."})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        display_name = validated_data.pop('display_name', '')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        ParentProfile.objects.create(user=user, display_name=display_name, is_active=True)
        return user


class ParentChildSerializer(serializers.ModelSerializer):
    """Read-only for linked parent-child; child summary when child is set."""
    child_id = serializers.SerializerMethodField()
    child_username = serializers.SerializerMethodField()
    child_name = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()
    overall_mastery = serializers.SerializerMethodField()
    total_xp = serializers.SerializerMethodField()
    invite_code = serializers.CharField(read_only=True)

    class Meta:
        model = ParentChild
        fields = ['id', 'parent', 'child_id', 'child_username', 'child_name', 'linked_at',
                  'last_active', 'overall_mastery', 'total_xp', 'invite_code']

    def get_child_id(self, obj):
        return obj.child_id if obj.child_id else None

    def get_child_username(self, obj):
        return obj.child.username if obj.child else None

    def get_child_name(self, obj):
        if obj.child:
            return obj.child.get_full_name() or obj.child.username
        return None

    def get_last_active(self, obj):
        if not obj.child:
            return None
        try:
            return obj.child.learning_profile.last_active
        except Exception:
            return None

    def get_overall_mastery(self, obj):
        if not obj.child:
            return None
        from .models import StudentProgress
        progress = StudentProgress.objects.filter(user=obj.child)
        if not progress.exists():
            return 0.0
        from django.db.models import Avg
        return round(progress.aggregate(avg=Avg('mastery_score'))['avg'] or 0, 3)

    def get_total_xp(self, obj):
        if not obj.child:
            return None
        try:
            return obj.child.xp_profile.total_xp
        except Exception:
            return 0