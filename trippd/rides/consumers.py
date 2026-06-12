import json
from json import JSONDecodeError
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import TripGroupMessage, TripGroup
from users.models import Profile
from html import escape
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        if self.user is None or not self.user.is_authenticated:
            print("Unauthenticated user tried to connect")
            await self.close(4003)
            return
        if not await self.user.trip_memberships.filter(trip__id=self.room_name, status="accepted").aexists():
            print("User is not a member of the trip group")
            await self.close(4003)
            return

        try:
            self.chat_data = await get_profile_and_group(self.user, self.room_name)

        except (TripGroup.DoesNotExist, Profile.DoesNotExist):
            print("Group or profile does not exist")
            await self.close(4004)
            return

        print(self.channel_name, "channel name")

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data["message"].strip()
            if not message:
                return
        except (JSONDecodeError, KeyError):
            print("Invalid message format")
            return

        msg = await TripGroupMessage.objects.acreate(
            sender=self.user, group=self.chat_data["group"], body=message
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": self.user.username,
                "avatar": self.chat_data["avatar"],
                "sent_at": timezone.localtime(msg.send_at).strftime("%I:%M %p"),
            },
        )

    async def chat_message(self, event):
        current_username = self.user.username

        if event["username"] == current_username:
            html = f"""
            <div class="chat chat-end">
              <div class="chat-header">
                  {escape(event['username'])}
                  <time class="text-xs opacity-50 ml-2">{event['sent_at']}</time>
                </div>
                <div class="chat-bubble">{escape(event['message'])}</div>
            </div>
            """

        else:
            html = f"""
            <div class="chat chat-start">
              <div class="chat-image avatar">
                      <div class="w-10 rounded-full">
                          <img src="{escape(event['avatar'])}" alt="avatar" />
                      </div>
                    </div>
                <div class="chat-header">
                  {escape(event['username'])}
                  <time class="text-xs opacity-50 ml-2">{event['sent_at']}</time>
                </div>
                <div class="chat-bubble">
                    {escape(event['message'])}
                </div>
            </div>
            """

        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message_html": html,
                }
            )
        )


async def get_profile_and_group(user, room_name):
    group = await TripGroup.objects.aget(trip=room_name)
    profile = await Profile.objects.aget(user=user)
    chat_data = {
        "group": group,
        "avatar": (
            profile.profile_picture.url
            if profile.profile_picture
            else f"https://ui-avatars.com/api/?name={ user.username }"
        ),
    }
    return chat_data
