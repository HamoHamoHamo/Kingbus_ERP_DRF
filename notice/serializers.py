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
	can_delete = serializers.ReadOnlyField()
	class Meta:
		model = NoticeComment
		fields = ['id', 'content', 'creator', 'can_delete', 'pub_date']
	
	# def get_can_delete(self, obj):
	# 	return 1 if self.request.user == self.creator else 0
		

	def to_representation(self, instance):
		representation = super().to_representation(instance)
		representation['can_delete'] = 1 if self.context['request'].user.id == representation['creator'] else 0
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

    is_read = serializers.SerializerMethodField() 

    class Meta:
        model = Notice
        fields = ['id', 'title', 'view_cnt', 'pub_date', 'creator', 'is_urgency', 'is_important', 'is_read']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['creator'] = (
            Member.objects.get(id=representation['creator']).name if representation['creator'] else None
        )

        representation['pub_date'] = str(representation['pub_date'])[:16].replace('T', ' ')

        return representation

    def get_is_read(self, obj):
        # 사용자와 NoticeViewCnt를 기준으로 읽음 여부 확인
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # NoticeViewCnt에서 해당 공지와 사용자 기준으로 읽음 여부 확인
            return NoticeViewCnt.objects.filter(notice_id=obj, user_id=request.user).exists()
        return False


class CommentSerializer(serializers.ModelSerializer):
	class Meta:
		model = NoticeComment
		fields = '__all__'

	def to_representation(self, instance):
		representation = super().to_representation(instance)
		representation['creator'] = Member.objects.get(id=representation['creator']).name if representation['creator'] else None
		representation['pub_date'] = str(representation['pub_date'])[:16].replace('T', ' ')
		return representation

# 공지 읽음 여부
class NoticeViewCntSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeViewCnt
        fields = ['notice_id', 'user_id', 'pub_date']  
        read_only_fields = ['pub_date'] 

