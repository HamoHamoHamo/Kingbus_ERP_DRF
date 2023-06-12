from datetime import datetime
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from .models import Notice, NoticeFile, NoticeComment, NoticeViewCnt
from vehicle.models import Vehicle
from humanresource.models import Member

class NoticeFileSerializer(serializers.ModelSerializer):
	class Meta:
		model = NoticeFile
		fields = ['file', 'filename']

class NoticeCommentSerializer(serializers.ModelSerializer):
	class Meta:
		model = NoticeComment
		fields = ['content', 'creator', 'pub_date']
	
	def to_representation(self, instance):
		representation = super().to_representation(instance)
		representation['creator'] = Member.objects.get(id=representation['creator']).name if representation['creator'] else None
		representation['pub_date'] = str(representation['pub_date'])[:16].replace('T', ' ')
		return representation
	
class NoticeSerializer(serializers.ModelSerializer):
	notice_file = NoticeFileSerializer(many=True, required=False)
	comment_user = NoticeCommentSerializer(many=True, required=False)
		
	class Meta:
		model = Notice
		fields = '__all__'
		
	def to_representation(self, instance):
		representation = super().to_representation(instance)
		representation['creator'] = Member.objects.get(id=representation['creator']).name if representation['creator'] else None
		representation['pub_date'] = str(representation['pub_date'])[:16].replace('T', ' ')
		return representation

class NoticeListSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notice
		fields = ['id', 'title', 'view_cnt', 'pub_date', 'creator']

	def to_representation(self, instance):
		representation = super().to_representation(instance)
		representation['creator'] = Member.objects.get(id=representation['creator']).name if representation['creator'] else None
		representation['pub_date'] = str(representation['pub_date'])[:16].replace('T', ' ')
		return representation

class CommentSerializer(serializers.ModelSerializer):
	class Meta:
		model = NoticeComment
		fields = '__all__'

	def to_representation(self, instance):
		representation = super().to_representation(instance)
		representation['creator'] = Member.objects.get(id=representation['creator']).name if representation['creator'] else None
		representation['pub_date'] = str(representation['pub_date'])[:16].replace('T', ' ')
		return representation

