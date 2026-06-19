import json
from json import JSONDecodeError
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import TripGroupMessage, TripGroup, ConversationMessage, Conversation
from users.models import Profile
from html import escape
from django.utils import timezone


async def get_profile_and_chat(user, room_name, chat_type):

    if chat_type == "trip":
        room = await TripGroup.objects.aget(trip=room_name)
    elif chat_type == "direct":
        room = await Conversation.objects.aget(id=room_name)
    else:
        raise ValueError("Invalid chat type. Must be 'trip' or 'direct'.")
    profile = await Profile.objects.aget(user=user)
    chat_data = {
        "room": room,
        "avatar": (
            profile.profile_picture.url
            if profile.profile_picture
            else f"https://ui-avatars.com/api/?name={ user.username }"
        ),
    }
    return chat_data


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handles new WebSocket connections, ensuring the user is authenticated and a member of the trip group."""
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        if self.user is None or not self.user.is_authenticated:
            print("Unauthenticated user tried to connect")
            await self.close(4003)
            return
        if not await self.user.trip_memberships.filter(
            trip__id=self.room_name, status="accepted"
        ).aexists():
            print("User is not a member of the trip group")
            await self.close(4003)
            return

        try:
            self.chat_data = await get_profile_and_chat(
                self.user, self.room_name, "trip"
            )

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
        """Handles incoming messages, saving them to the database and broadcasting to the group."""
        try:
            data = json.loads(text_data)
            message = data["message"].strip()
            if not message:
                return
        except (JSONDecodeError, KeyError):
            print("Invalid message format")
            return

        msg = await TripGroupMessage.objects.acreate(
            sender=self.user, group=self.chat_data["room"], body=message
        )

        print("Message saved:", msg)

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
        """Receives messages from the group and sends them to the WebSocket client."""
        print("Received event:", event)
        current_username = self.user.username

        html = f"""
        <div class="chat {'chat-end' if event['username'] == current_username else 'chat-start'}">
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

    async def trip_activity(self, event):
        """Handles activity updates"""
        print("Received activity event:", event)
        html = f"""
         <div class="flex justify-center my-4">
                  <div class="badge badge-soft">{escape(event['activity'])}</div>
                </div>
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "trip_activity",
                    "message_html": html,
                }
            )
        )


class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user is None or not self.user.is_authenticated:
            print("Unauthenticated user tried to connect to direct messages")
            await self.close(4003)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"dm_{self.conversation_id}"

        if not await self.user.conversations.filter(id=self.conversation_id).aexists():
            print("User is not a participant in the conversation")
            await self.close(4003)
            return

        try:
            self.chat_data = await get_profile_and_chat(
                self.user, self.conversation_id, "direct"
            )
        except (Conversation.DoesNotExist, Profile.DoesNotExist):
            print("Conversation or profile does not exist")
            await self.close(4004)
            return

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
            print("Invalid message format in direct message")
            return

        msg = await ConversationMessage.objects.acreate(
            conversation=self.chat_data["room"], sender=self.user, body=message
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "dm_message",
                "message": message,
                "username": self.user.username,
                "sent_at": timezone.localtime(msg.sent_at).strftime("%I:%M %p"),
                "avatar": self.chat_data["avatar"],
            },
        )

    async def dm_message(self, event):
        print("Received DM event:", event)
        html = f"""
        <div class="chat {'chat-end' if event['username'] == self.user.username else 'chat-start'}">
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
        print("Sending DM HTML:", html)
        await self.send(
            text_data=json.dumps(
                {
                    "type": "dm_message",
                    "message_html": html,
                }
            )
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user is None or not self.user.is_authenticated:
            print("Unauthenticated user tried to connect to notifications")
            await self.close(4003)
            return

        self.room_group_name = f"notifications_{self.user.id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_notification(self, event):
        """Handles sending notifications to the user."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "message": event["message"],
                }
            )
        )
