from django.urls import path
from .views import (
    # Auth views
    AIDoubtAssistantView, GetConceptResourcesView, RegisterView, LoginView, DashboardView,
    
    # Concept management
    ConceptListView, GenerateConceptView,
    SuggestSubjectsView, SuggestConceptsView,
    
    # Teaching-first flow views
    StartTeachingSessionView, GetTeachingContentView,
    GenerateQuestionsFromTeachingView, SubmitAtomAnswerView,
    CompleteAtomView, GetLearningProgressView,
    GenerateInitialQuizView, SubmitInitialQuizAnswerView, CompleteInitialQuizView,
    GenerateFinalChallengeView, CompleteFinalChallengeView,

    # Adaptive flow views
    GenerateConceptOverviewView, GenerateAtomSummaryView,
    AdaptiveReteachView, GetAllAtomsMasteryView,
    GetNextLearningStepView,

    # Enhanced pacing engine views
    GetVelocityGraphView, GetFatigueStatusView, RecordBreakView,
    RetentionCheckView, RecordHintUsageView,

    # Leaderboard views
    LeaderboardView, MyXPView,

    # Concept final challenge views
    GenerateConceptFinalChallengeView, SubmitConceptFinalAnswerView,
    CompleteConceptFinalChallengeView,

    # Teacher views
    TeacherRegisterView, TeacherLoginView, TeacherDashboardView,
    TeacherStudentListView, TeacherStudentDetailView,
    TeacherContentListView, TeacherContentDetailView,
    TeacherQuestionListView, TeacherQuestionApproveView, TeacherAddQuestionView,
    TeacherOverrideListView, TeacherOverrideDeactivateView,
    TeacherGoalListView, TeacherGoalUpdateView,
    TeacherClassAnalyticsView,
    TeacherConceptManageView, TeacherAtomManageView,
    CheckTeacherView,
    # Parent views
    ParentRegisterView, ParentLoginView, CheckParentView,
    ParentChildrenView, ParentLinkChildView, ParentInviteCodeView,
    ParentChildInsightsView,
    LinkParentView,

    # AI planner views 
    CreateStudyPlannerView , GetMyPlannerView, TodayStudyView
)

urlpatterns = [
    # Auth endpoints
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Concept management
    path('api/concepts/', ConceptListView.as_view(), name='concepts'),
    path('api/generate-concept/', GenerateConceptView.as_view(), name='generate_concept'),
    path('api/suggest-subjects/', SuggestSubjectsView.as_view(), name='suggest_subjects'),
    path('api/suggest-concepts/', SuggestConceptsView.as_view(), name='suggest_concepts'),
    
    # Teaching-first flow endpoints
    path('api/start-teaching-session/', StartTeachingSessionView.as_view(), name='start_teaching_session'),
    path('api/initial-quiz/', GenerateInitialQuizView.as_view(), name='generate_initial_quiz'),
    path('api/submit-initial-quiz-answer/', SubmitInitialQuizAnswerView.as_view(), name='submit_initial_quiz_answer'),
    path('api/complete-initial-quiz/', CompleteInitialQuizView.as_view(), name='complete_initial_quiz'),
    path('api/teaching-content/', GetTeachingContentView.as_view(), name='teaching_content'),
    path('api/generate-questions-from-teaching/', GenerateQuestionsFromTeachingView.as_view(), name='generate_questions_from_teaching'),
    path('api/submit-atom-answer/', SubmitAtomAnswerView.as_view(), name='submit_atom_answer'),
    path('api/complete-atom/', CompleteAtomView.as_view(), name='complete_atom'),
    path('api/final-challenge/', GenerateFinalChallengeView.as_view(), name='generate_final_challenge'),
    path('api/complete-final-challenge/', CompleteFinalChallengeView.as_view(), name='complete_final_challenge'),
    
    # Adaptive flow endpoints
    path('api/concept-overview/', GenerateConceptOverviewView.as_view(), name='concept_overview'),
    path('api/atom-summary/', GenerateAtomSummaryView.as_view(), name='atom_summary'),
    path('api/adaptive-reteach/', AdaptiveReteachView.as_view(), name='adaptive_reteach'),
    path('api/all-atoms-mastery/', GetAllAtomsMasteryView.as_view(), name='all_atoms_mastery'),
    path('api/next-learning-step/', GetNextLearningStepView.as_view(), name='next_learning_step'),

    # Progress
    path('api/progress/', GetLearningProgressView.as_view(), name='learning_progress'),
    
    path('api/concept-resources/', GetConceptResourcesView.as_view(), name='concept_resources'),

    # Enhanced pacing engine endpoints
    path('api/velocity-graph/', GetVelocityGraphView.as_view(), name='velocity_graph'),
    path('api/fatigue-status/', GetFatigueStatusView.as_view(), name='fatigue_status'),
    path('api/record-break/', RecordBreakView.as_view(), name='record_break'),
    path('api/retention-check/', RetentionCheckView.as_view(), name='retention_check'),
    path('api/record-hint/', RecordHintUsageView.as_view(), name='record_hint'),

    # Leaderboard endpoints
    path('api/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('api/my-xp/', MyXPView.as_view(), name='my_xp'),

    # Concept final challenge endpoints
    path('api/concept-final-challenge/', GenerateConceptFinalChallengeView.as_view(), name='generate_concept_final_challenge'),
    path('api/submit-concept-final-answer/', SubmitConceptFinalAnswerView.as_view(), name='submit_concept_final_answer'),
    path('api/complete-concept-final-challenge/', CompleteConceptFinalChallengeView.as_view(), name='complete_concept_final_challenge'),
    path("ai-assistant/", AIDoubtAssistantView.as_view(), name="ai_assistant"),

    # ==================== TEACHER ENDPOINTS ====================
    path('api/teacher/register/', TeacherRegisterView.as_view(), name='teacher_register'),
    path('api/teacher/login/', TeacherLoginView.as_view(), name='teacher_login'),
    path('api/teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('api/teacher/check/', CheckTeacherView.as_view(), name='check_teacher'),

    # Student analytics
    path('api/teacher/students/', TeacherStudentListView.as_view(), name='teacher_students'),
    path('api/teacher/student-detail/', TeacherStudentDetailView.as_view(), name='teacher_student_detail'),

    # Content management
    path('api/teacher/content/', TeacherContentListView.as_view(), name='teacher_content'),
    path('api/teacher/content-detail/', TeacherContentDetailView.as_view(), name='teacher_content_detail'),

    # Question management
    path('api/teacher/questions/', TeacherQuestionListView.as_view(), name='teacher_questions'),
    path('api/teacher/question-approve/', TeacherQuestionApproveView.as_view(), name='teacher_question_approve'),
    path('api/teacher/question-add/', TeacherAddQuestionView.as_view(), name='teacher_add_question'),

    # Student intervention
    path('api/teacher/overrides/', TeacherOverrideListView.as_view(), name='teacher_overrides'),
    path('api/teacher/override-deactivate/', TeacherOverrideDeactivateView.as_view(), name='teacher_override_deactivate'),

    # Goals & deadlines
    path('api/teacher/goals/', TeacherGoalListView.as_view(), name='teacher_goals'),
    path('api/teacher/goal-update/', TeacherGoalUpdateView.as_view(), name='teacher_goal_update'),

    # Class analytics
    path('api/teacher/class-analytics/', TeacherClassAnalyticsView.as_view(), name='teacher_class_analytics'),

    # Knowledge graph management
    path('api/teacher/concepts/', TeacherConceptManageView.as_view(), name='teacher_concepts'),
    path('api/teacher/atoms/', TeacherAtomManageView.as_view(), name='teacher_atoms'),
    
    # ==================== PARENT ENDPOINTS ====================
    path('api/parent/register/', ParentRegisterView.as_view(), name='parent_register'),
    path('api/parent/login/', ParentLoginView.as_view(), name='parent_login'),
    path('api/parent/check/', CheckParentView.as_view(), name='parent_check'),
    path('api/parent/children/', ParentChildrenView.as_view(), name='parent_children'),
    path('api/parent/link-child/', ParentLinkChildView.as_view(), name='parent_link_child'),
    path('api/parent/invite-code/', ParentInviteCodeView.as_view(), name='parent_invite_code'),
    path('api/parent/child/<int:child_id>/insights/', ParentChildInsightsView.as_view(), name='parent_child_insights'),

    # Student links to parent (invite code)
    path('api/link-parent/', LinkParentView.as_view(), name='link_parent'),

    # AI planner 
    path('create-planner/', CreateStudyPlannerView.as_view(), name='create_planner'),
    path('my-planner/', GetMyPlannerView.as_view(), name='my_planner'),
    path("today-study/", TodayStudyView.as_view(), name="today_study"),

]