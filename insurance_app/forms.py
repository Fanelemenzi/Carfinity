from django import forms
from django.contrib.auth.models import User
from assessments.models import AssessmentComment
from .models import AssessmentNotification


class AssessmentCommentForm(forms.ModelForm):
    """Form for creating assessment comments and feedback"""
    
    class Meta:
        model = AssessmentComment
        fields = ['comment_type', 'subject', 'content', 'is_important', 'requires_action', 'is_customer_visible']
        widgets = {
            'comment_type': forms.Select(
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
                }
            ),
            'subject': forms.TextInput(
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                    'placeholder': 'Brief subject line (optional)'
                }
            ),
            'content': forms.Textarea(
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                    'rows': 4,
                    'placeholder': 'Enter your comment or feedback...'
                }
            ),
            'is_important': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded'
                }
            ),
            'requires_action': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-orange-600 focus:ring-orange-500 border-gray-300 rounded'
                }
            ),
            'is_customer_visible': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                }
            ),
        }
        labels = {
            'comment_type': 'Comment Type',
            'subject': 'Subject',
            'content': 'Comment',
            'is_important': 'Mark as Important',
            'requires_action': 'Requires Action',
            'is_customer_visible': 'Visible to Customer',
        }
        help_texts = {
            'content': 'Provide detailed feedback or comments about this assessment.',
            'is_important': 'Check this box to mark this comment as important.',
            'requires_action': 'Check this box if this comment requires follow-up action.',
            'is_customer_visible': 'Check this box if the customer should be able to see this comment.',
        }


class CommentReplyForm(forms.ModelForm):
    """Form for replying to existing comments"""
    
    class Meta:
        model = AssessmentComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                    'rows': 3,
                    'placeholder': 'Enter your reply...'
                }
            ),
        }
        labels = {
            'content': 'Reply',
        }


class CommentResolutionForm(forms.ModelForm):
    """Form for resolving comments that require action"""
    
    class Meta:
        model = AssessmentComment
        fields = ['requires_action']
        widgets = {
            'requires_action': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded'
                }
            ),
        }
        labels = {
            'requires_action': 'Mark as Resolved (no action required)',
        }