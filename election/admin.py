from django.contrib import admin
from .models import Election, Candidate, Vote, Feedback

class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1

class ElectionAdmin(admin.ModelAdmin):
    inlines = [CandidateInline]
    list_display = ('title', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('title',)

class VoteAdmin(admin.ModelAdmin):
    list_display = ('election', 'candidate', 'voter', 'timestamp')
    list_filter = ('election',)
    search_fields = ('voter__username', 'candidate__name')
    readonly_fields = ('election', 'candidate', 'voter', 'timestamp') # Votes should be immutable

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    readonly_fields = ('submitted_at',)

admin.site.register(Election, ElectionAdmin)
admin.site.register(Candidate)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Feedback, FeedbackAdmin)
