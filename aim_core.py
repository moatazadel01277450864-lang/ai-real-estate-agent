# ============================================================
# AIM CORE
# المحرك الأساسي لوكيل الذكاء الاصطناعي
#
# Architecture:
# - Multi-Tenant
# - Roles & Permissions
# - Channel Abstraction
# - Unique IDs
# - Conversation Sessions
# - Customer Memory
# - Catalog Management
# - Lead / Customer Lifecycle
# - Order Versioning
# - Event System
# - Integration Layer
# - Feature Flags
# - Business Configuration
# - Custom Fields
# - Media Objects
# - Audit Log
# - API / Webhook Structure
# - Usage Tracking
# - Business Onboarding Wizard
# - Database abstraction foundation
# - Multilingual foundation
# - Analytics foundation
# - Background job foundation
# - Security foundation
#
# IMPORTANT:
# هذا الملف لا يعتمد على Gemini أو Google Sheets أو WhatsApp.
# الـCore مستقل، والـIntegrations يتم تركيبها من الخارج.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import copy
import json
import uuid

from database import Database


# ============================================================
# 1. UTILITIES
# أدوات مساعدة
# ============================================================

def utc_now() -> str:
    """إرجاع الوقت الحالي بصيغة UTC."""
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str = "id") -> str:
    """إنشاء ID فريد."""
    return f"{prefix}_{uuid.uuid4().hex}"


def deep_copy(data: Any) -> Any:
    """نسخة مستقلة من البيانات."""
    return copy.deepcopy(data)


# ============================================================
# 2. FEATURE FLAGS
# تشغيل / إيقاف مميزات النظام
# ============================================================

FEATURES = {
    # Core
    "multi_tenant": True,
    "customer_memory": True,
    "conversation_history": True,
    "catalog": True,
    "lead_management": True,
    "customer_lifecycle": True,
    "human_handoff": True,
    "order_management": True,

    # AI / Media
    "image_analysis": True,
    "voice_transcription": True,
    "file_messages": True,

    # Communication
    "whatsapp": True,
    "facebook": True,
    "instagram": True,
    "email": True,

    # Automation
    "follow_up": True,
    "reports": True,

    # Architecture
    "roles_permissions": True,
    "channel_abstraction": True,
    "events": True,
    "integrations": True,
    "custom_fields": True,
    "audit_log": True,
    "api": True,
    "webhooks": True,
    "usage_tracking": True,
    "onboarding": True,

    # Future-ready foundations
    "analytics": True,
    "background_jobs": True,
    "database_abstraction": True,
    "multilingual": True,
    "security": True,
}


# ============================================================
# 3. PLAN DEFINITIONS
# خطط مستقبلية لتشغيل / إيقاف المميزات
#
# لا يوجد هنا أسعار.
# فقط صلاحيات Features.
# ============================================================

PLAN_DEFINITIONS = {

    "starter": {
        "customer_memory",
        "conversation_history",
        "catalog",
        "lead_management",
        "customer_lifecycle",
        "human_handoff",
        "roles_permissions",
        "channel_abstraction",
        "usage_tracking",
        "onboarding",
    },

    "business": {
        "customer_memory",
        "conversation_history",
        "catalog",
        "lead_management",
        "customer_lifecycle",
        "human_handoff",
        "order_management",
        "image_analysis",
        "voice_transcription",
        "follow_up",
        "reports",
        "roles_permissions",
        "channel_abstraction",
        "events",
        "integrations",
        "custom_fields",
        "audit_log",
        "api",
        "webhooks",
        "usage_tracking",
        "onboarding",
        "analytics",
    },

    "enterprise": set(FEATURES.keys()),
}


class FeatureManager:

    def __init__(self):
        self.features = dict(FEATURES)

    def is_enabled(self, feature: str) -> bool:
        return bool(self.features.get(feature, False))

    def enable(self, feature: str):
        self.features[feature] = True

    def disable(self, feature: str):
        self.features[feature] = False

    def set_feature(self, feature: str, enabled: bool):
        self.features[feature] = bool(enabled)

    def apply_plan(self, plan_name: str):
        plan_features = PLAN_DEFINITIONS.get(plan_name)

        if plan_features is None:
            raise ValueError(f"الخطة غير موجودة: {plan_name}")

        for feature in FEATURES:
            self.features[feature] = feature in plan_features

    def get_all(self) -> Dict[str, bool]:
        return dict(self.features)


# ============================================================
# 4. ROLES & PERMISSIONS
# ============================================================

ROLE_PERMISSIONS = {

    "owner": {
        "*",
    },

    "admin": {
        "business.read",
        "business.update",
        "customer.read",
        "customer.write",
        "conversation.read",
        "conversation.write",
        "catalog.read",
        "catalog.write",
        "lead.read",
        "lead.write",
        "order.read",
        "order.write",
        "employee.read",
        "employee.write",
        "integration.read",
        "integration.write",
        "reports.read",
        "audit.read",
        "settings.read",
        "settings.write",
    },

    "employee": {
        "customer.read",
        "customer.write",
        "conversation.read",
        "conversation.write",
        "catalog.read",
        "lead.read",
        "lead.write",
        "order.read",
        "order.write",
        "reports.read",
    },

    "viewer": {
        "customer.read",
        "conversation.read",
        "catalog.read",
        "lead.read",
        "order.read",
        "reports.read",
    },
}


@dataclass
class User:
    user_id: str
    business_id: str
    name: str
    role: str = "employee"
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class PermissionManager:

    def __init__(self):
        self.users: Dict[str, User] = {}

    def add_user(
        self,
        business_id: str,
        name: str,
        role: str = "employee",
        user_id: Optional[str] = None,
    ) -> User:

        if role not in ROLE_PERMISSIONS:
            raise ValueError(f"الدور غير موجود: {role}")

        user = User(
            user_id=user_id or generate_id("usr"),
            business_id=business_id,
            name=name,
            role=role,
        )

        self.users[user.user_id] = user

        return user

    def check_permission(
        self,
        user_id: str,
        permission: str,
        business_id: str,
    ) -> bool:

        user = self.users.get(user_id)

        if not user:
            return False

        if not user.active:
            return False

        if user.business_id != business_id:
            return False

        permissions = ROLE_PERMISSIONS.get(user.role, set())

        return "*" in permissions or permission in permissions


# ============================================================
# 5. BUSINESS
# Multi-Tenant + Business Configuration
# ============================================================

@dataclass
class Business:
    business_id: str
    name: str
    business_type: str = "general"

    language: str = "ar"
    currency: str = "EGP"
    timezone: str = "Africa/Cairo"

    config: Dict[str, Any] = field(default_factory=dict)

    feature_flags: Dict[str, bool] = field(
        default_factory=lambda: dict(FEATURES)
    )

    custom_field_definitions: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )

    onboarding_data: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(default_factory=utc_now)


class BusinessManager:

    def __init__(self):
        self.businesses: Dict[str, Business] = {}

    def create_business(
        self,
        name: str,
        business_type: str = "general",
        business_id: Optional[str] = None,
    ) -> Business:

        business = Business(
            business_id=business_id or generate_id("biz"),
            name=name,
            business_type=business_type,
        )

        self.businesses[business.business_id] = business

        return business

    def get_business(self, business_id: str) -> Optional[Business]:
        return self.businesses.get(business_id)

    def require_business(self, business_id: str) -> Business:

        business = self.get_business(business_id)

        if not business:
            raise ValueError(
                f"Business غير موجود: {business_id}"
            )

        return business

    def update_config(
        self,
        business_id: str,
        config: Dict[str, Any],
    ):

        business = self.require_business(business_id)

        business.config.update(deep_copy(config))

    def set_feature(
        self,
        business_id: str,
        feature: str,
        enabled: bool,
    ):

        business = self.require_business(business_id)

        business.feature_flags[feature] = bool(enabled)


# ============================================================
# 6. CUSTOMER
# Customer Memory + Lifecycle
# ============================================================

CUSTOMER_STATUSES = {
    "new",
    "interested",
    "qualified",
    "customer",
    "not_interested",
    "human_handoff",
}


@dataclass
class Customer:
    customer_id: str
    business_id: str

    name: str = ""
    phone: str = ""
    email: str = ""

    status: str = "new"
    interest_score: int = 0

    data: Dict[str, Any] = field(default_factory=dict)

    custom_fields: Dict[str, Any] = field(
        default_factory=dict
    )

    tags: List[str] = field(default_factory=list)

    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


class CustomerManager:

    def __init__(self):
        self.customers: Dict[str, Customer] = {}

    def create_customer(
        self,
        business_id: str,
        name: str = "",
        phone: str = "",
        customer_id: Optional[str] = None,
    ) -> Customer:

        customer = Customer(
            customer_id=customer_id or generate_id("cus"),
            business_id=business_id,
            name=name,
            phone=phone,
        )

        self.customers[customer.customer_id] = customer

        return customer

    def get_customer(
        self,
        business_id: str,
        customer_id: str,
    ) -> Optional[Customer]:

        customer = self.customers.get(customer_id)

        if not customer:
            return None

        if customer.business_id != business_id:
            return None

        return customer

    def update_customer(
        self,
        business_id: str,
        customer_id: str,
        data: Dict[str, Any],
    ):

        customer = self.get_customer(
            business_id,
            customer_id,
        )

        if not customer:
            raise ValueError("العميل غير موجود")

        for key, value in data.items():

            if value is None or value == "":
                continue

            if hasattr(customer, key):

                if key not in {
                    "data",
                    "custom_fields",
                    "tags",
                }:

                    setattr(customer, key, value)

            else:
                customer.data[key] = value

        customer.updated_at = utc_now()

    def set_status(
        self,
        business_id: str,
        customer_id: str,
        status: str,
    ):

        if status not in CUSTOMER_STATUSES:
            raise ValueError(
                f"Customer status غير صالح: {status}"
            )

        customer = self.get_customer(
            business_id,
            customer_id,
        )

        if not customer:
            raise ValueError("العميل غير موجود")

        customer.status = status
        customer.updated_at = utc_now()


# ============================================================
# 7. MEDIA OBJECT
# Image / Audio / File / Text
# ============================================================

MEDIA_TYPES = {
    "text",
    "image",
    "audio",
    "file",
}


@dataclass
class MediaObject:
    media_id: str

    type: str

    url: str = ""
    file_name: str = ""
    mime_type: str = ""

    size: Optional[int] = None

    transcript: str = ""
    analysis: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(default_factory=utc_now)


class MediaManager:

    def __init__(self):
        self.media: Dict[str, MediaObject] = {}

    def create_media(
        self,
        media_type: str,
        url: str = "",
        file_name: str = "",
        mime_type: str = "",
        size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MediaObject:

        if media_type not in MEDIA_TYPES:
            raise ValueError(
                f"نوع Media غير مدعوم: {media_type}"
            )

        media = MediaObject(
            media_id=generate_id("media"),
            type=media_type,
            url=url,
            file_name=file_name,
            mime_type=mime_type,
            size=size,
            metadata=metadata or {},
        )

        self.media[media.media_id] = media
        return media

    def get_media(
        self,
        media_id: str,
    ) -> Optional[MediaObject]:
        return self.media.get(media_id)

    def list_media(self) -> List[MediaObject]:
        return list(self.media.values())

    def add_transcript(
        self,
        media: MediaObject,
        transcript: str,
    ):

        media.transcript = transcript

    def add_analysis(
        self,
        media: MediaObject,
        analysis: Dict[str, Any],
    ):

        media.analysis.update(
            deep_copy(analysis)
        )


# ============================================================
# 8. CONVERSATIONS
# Sessions + Channels + Messages
# ============================================================

SUPPORTED_CHANNELS = {
    "web",
    "whatsapp",
    "facebook",
    "instagram",
    "email",
    "phone",
    "api",
    "internal",
}


@dataclass
class Message:
    message_id: str
    business_id: str
    conversation_id: str
    customer_id: str

    role: str
    content: str

    channel: str = "web"

    media: List[Dict[str, Any]] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(default_factory=utc_now)


@dataclass
class ConversationSession:
    conversation_id: str
    business_id: str
    customer_id: str

    channel: str = "web"

    active: bool = True

    messages: List[Message] = field(
        default_factory=list
    )

    shown_items: List[str] = field(
        default_factory=list
    )

    context: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


class ConversationManager:

    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}

    def create_session(
        self,
        business_id: str,
        customer_id: str,
        channel: str = "web",
    ) -> ConversationSession:

        if channel not in SUPPORTED_CHANNELS:
            raise ValueError(
                f"Channel غير مدعوم: {channel}"
            )

        session = ConversationSession(
            conversation_id=generate_id("conv"),
            business_id=business_id,
            customer_id=customer_id,
            channel=channel,
        )

        self.sessions[session.conversation_id] = session

        return session

    def get_session(
        self,
        business_id: str,
        conversation_id: str,
    ) -> Optional[ConversationSession]:

        session = self.sessions.get(conversation_id)

        if not session:
            return None

        if session.business_id != business_id:
            return None

        return session

    def add_message(
        self,
        business_id: str,
        conversation_id: str,
        role: str,
        content: str,
        media: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:

        session = self.get_session(
            business_id,
            conversation_id,
        )

        if not session:
            raise ValueError("Conversation غير موجودة")

        message = Message(
            message_id=generate_id("msg"),
            business_id=business_id,
            conversation_id=conversation_id,
            customer_id=session.customer_id,
            role=role,
            content=content,
            channel=session.channel,
            media=media or [],
            metadata=metadata or {},
        )

        session.messages.append(message)
        session.updated_at = utc_now()

        return message


# ============================================================
# 9. CATALOG
# Products / Services / Properties
# ============================================================

@dataclass
class CatalogItem:
    item_id: str
    business_id: str

    name: str
    item_type: str = "product"

    price: Optional[float] = None

    data: Dict[str, Any] = field(
        default_factory=dict
    )

    active: bool = True

    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


class CatalogManager:

    def __init__(self):
        self.items: Dict[str, CatalogItem] = {}

    def add_item(
        self,
        business_id: str,
        name: str,
        item_type: str = "product",
        price: Optional[float] = None,
        data: Optional[Dict[str, Any]] = None,
        item_id: Optional[str] = None,
    ) -> CatalogItem:

        item = CatalogItem(
            item_id=item_id or generate_id("item"),
            business_id=business_id,
            name=name,
            item_type=item_type,
            price=price,
            data=data or {},
        )

        self.items[item.item_id] = item

        return item

    def get_item(
        self,
        business_id: str,
        item_id: str,
    ) -> Optional[CatalogItem]:

        item = self.items.get(item_id)

        if not item:
            return None

        if item.business_id != business_id:
            return None

        return item

    def list_items(
        self,
        business_id: str,
        active_only: bool = True,
    ) -> List[CatalogItem]:

        result = []

        for item in self.items.values():

            if item.business_id != business_id:
                continue

            if active_only and not item.active:
                continue

            result.append(item)

        return result


# ============================================================
# 10. ORDERS
# Order Versioning + Prevent Mixing Old/New Orders
# ============================================================

ORDER_STATUSES = {
    "draft",
    "pending",
    "confirmed",
    "processing",
    "completed",
    "cancelled",
}


@dataclass
class OrderVersion:
    version_id: str
    order_id: str
    version_number: int

    data: Dict[str, Any]

    changed_by: str = "system"

    created_at: str = field(default_factory=utc_now)


@dataclass
class Order:
    order_id: str
    business_id: str
    customer_id: str

    status: str = "draft"

    current_version: int = 1

    data: Dict[str, Any] = field(
        default_factory=dict
    )

    versions: List[OrderVersion] = field(
        default_factory=list
    )

    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


class OrderManager:

    def __init__(self):
        self.orders: Dict[str, Order] = {}

    def create_order(
        self,
        business_id: str,
        customer_id: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Order:

        order = Order(
            order_id=generate_id("ord"),
            business_id=business_id,
            customer_id=customer_id,
            data=data or {},
        )

        version = OrderVersion(
            version_id=generate_id("ordv"),
            order_id=order.order_id,
            version_number=1,
            data=deep_copy(order.data),
        )

        order.versions.append(version)

        self.orders[order.order_id] = order

        return order

    def get_order(
        self,
        business_id: str,
        order_id: str,
    ) -> Optional[Order]:

        order = self.orders.get(order_id)

        if not order:
            return None

        if order.business_id != business_id:
            return None

        return order

    def update_order(
        self,
        business_id: str,
        order_id: str,
        changes: Dict[str, Any],
        changed_by: str = "system",
    ) -> Order:

        order = self.get_order(
            business_id,
            order_id,
        )

        if not order:
            raise ValueError("Order غير موجود")

        order.data.update(
            deep_copy(changes)
        )

        order.current_version += 1
        order.updated_at = utc_now()

        version = OrderVersion(
            version_id=generate_id("ordv"),
            order_id=order.order_id,
            version_number=order.current_version,
            data=deep_copy(order.data),
            changed_by=changed_by,
        )

        order.versions.append(version)

        return order

    def set_status(
        self,
        business_id: str,
        order_id: str,
        status: str,
    ):

        if status not in ORDER_STATUSES:
            raise ValueError(
                f"Order status غير صالح: {status}"
            )

        self.update_order(
            business_id,
            order_id,
            {"status": status},
        )

        order = self.get_order(
            business_id,
            order_id,
        )

        order.status = status


# ============================================================
# 11. LEADS
# ============================================================

@dataclass
class Lead:
    lead_id: str
    business_id: str
    customer_id: str

    status: str = "new"
    interest_score: int = 0

    data: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


class LeadManager:

    def __init__(self):
        self.leads: Dict[str, Lead] = {}

    def create_or_update_lead(
        self,
        business_id: str,
        customer_id: str,
        status: str,
        interest_score: int,
        data: Optional[Dict[str, Any]] = None,
    ) -> Lead:

        existing = None

        for lead in self.leads.values():

            if (
                lead.business_id == business_id
                and lead.customer_id == customer_id
            ):
                existing = lead
                break

        if existing:

            existing.status = status
            existing.interest_score = interest_score

            if data:
                existing.data.update(
                    deep_copy(data)
                )

            existing.updated_at = utc_now()

            return existing

        lead = Lead(
            lead_id=generate_id("lead"),
            business_id=business_id,
            customer_id=customer_id,
            status=status,
            interest_score=interest_score,
            data=data or {},
        )

        self.leads[lead.lead_id] = lead

        return lead


# ============================================================
# 12. EVENTS
# Event-Driven Architecture
# ============================================================

@dataclass
class Event:
    event_id: str
    business_id: str

    event_type: str

    payload: Dict[str, Any] = field(
        default_factory=dict
    )

    actor_id: str = "system"

    created_at: str = field(default_factory=utc_now)


class EventManager:

    def __init__(self):
        self.events: List[Event] = []
        self.listeners: Dict[
            str,
            List[Callable[[Event], None]]
        ] = {}

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], None],
    ):

        self.listeners.setdefault(
            event_type,
            []
        ).append(callback)

    def emit(
        self,
        business_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        actor_id: str = "system",
    ) -> Event:

        event = Event(
            event_id=generate_id("evt"),
            business_id=business_id,
            event_type=event_type,
            payload=payload or {},
            actor_id=actor_id,
        )

        self.events.append(event)

        callbacks = (
            self.listeners.get(event_type, [])
            + self.listeners.get("*", [])
        )

        for callback in callbacks:

            try:
                callback(event)
            except Exception:
                # لا نوقف الـCore بسبب Listener خارجي
                pass

        return event


# ============================================================
# 13. INTEGRATION LAYER
# WhatsApp / Facebook / Instagram / Email / etc.
# ============================================================

@dataclass
class Integration:
    integration_id: str
    business_id: str

    name: str
    integration_type: str

    enabled: bool = False

    config: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(default_factory=utc_now)


class IntegrationManager:

    def __init__(self):
        self.integrations: Dict[str, Integration] = {}

    def register(
        self,
        business_id: str,
        name: str,
        integration_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Integration:

        integration = Integration(
            integration_id=generate_id("int"),
            business_id=business_id,
            name=name,
            integration_type=integration_type,
            config=config or {},
        )

        self.integrations[
            integration.integration_id
        ] = integration

        return integration

    def enable(
        self,
        business_id: str,
        integration_id: str,
    ):

        integration = self.integrations.get(
            integration_id
        )

        if not integration:
            raise ValueError(
                "Integration غير موجودة"
            )

        if integration.business_id != business_id:
            raise PermissionError(
                "لا يمكن الوصول إلى Integration تخص Business آخر"
            )

        integration.enabled = True

    def disable(
        self,
        business_id: str,
        integration_id: str,
    ):

        integration = self.integrations.get(
            integration_id
        )

        if not integration:
            raise ValueError(
                "Integration غير موجودة"
            )

        if integration.business_id != business_id:
            raise PermissionError(
                "لا يمكن الوصول إلى Integration تخص Business آخر"
            )

        integration.enabled = False


# ============================================================
# 14. CUSTOM FIELDS
# ============================================================

class CustomFieldManager:

    def __init__(self):
        self.schemas: Dict[
            str,
            Dict[str, Dict[str, Any]]
        ] = {}

        self.values: Dict[
            str,
            Dict[str, Dict[str, Any]]
        ] = {}

    def define_field(
        self,
        business_id: str,
        field_name: str,
        field_type: str = "text",
        required: bool = False,
    ):

        self.schemas.setdefault(
            business_id,
            {}
        )[field_name] = {
            "name": field_name,
            "type": field_type,
            "required": required,
        }

    def set_value(
        self,
        business_id: str,
        entity_id: str,
        field_name: str,
        value: Any,
    ):

        schema = self.schemas.get(
            business_id,
            {}
        )

        if field_name not in schema:
            raise ValueError(
                f"Custom field غير معرف: {field_name}"
            )

        self.values.setdefault(
            entity_id,
            {}
        )[field_name] = value

    def get_values(
        self,
        business_id: str,
        entity_id: str,
    ) -> Dict[str, Any]:

        # التأكد أن الـEntity تابع للـBusiness
        # يتم في الطبقة الأعلى قبل الاستخدام.

        return deep_copy(
            self.values.get(
                entity_id,
                {}
            )
        )


# ============================================================
# 15. AUDIT LOG
# ============================================================

@dataclass
class AuditEntry:
    audit_id: str
    business_id: str

    action: str
    resource_type: str
    resource_id: str

    actor_id: str = "system"

    details: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(default_factory=utc_now)


class AuditManager:

    def __init__(self):
        self.entries: List[AuditEntry] = []

    def log(
        self,
        business_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_id: str = "system",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:

        entry = AuditEntry(
            audit_id=generate_id("audit"),
            business_id=business_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=actor_id,
            details=details or {},
        )

        self.entries.append(entry)

        return entry

    def list_business_entries(
        self,
        business_id: str,
    ) -> List[AuditEntry]:

        return [
            entry
            for entry in self.entries
            if entry.business_id == business_id
        ]


# ============================================================
# 16. API + WEBHOOK STRUCTURE
# ============================================================

@dataclass
class Webhook:
    webhook_id: str
    business_id: str

    url: str
    event_types: List[str]

    active: bool = True

    secret: str = field(
        default_factory=lambda: uuid.uuid4().hex
    )

    created_at: str = field(default_factory=utc_now)


class APIManager:

    def __init__(self):
        self.webhooks: Dict[str, Webhook] = {}

    def register_webhook(
        self,
        business_id: str,
        url: str,
        event_types: List[str],
    ) -> Webhook:

        webhook = Webhook(
            webhook_id=generate_id("wh"),
            business_id=business_id,
            url=url,
            event_types=event_types,
        )

        self.webhooks[
            webhook.webhook_id
        ] = webhook

        return webhook

    def create_event_payload(
        self,
        event: Event,
    ) -> Dict[str, Any]:

        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "business_id": event.business_id,
            "actor_id": event.actor_id,
            "payload": deep_copy(event.payload),
            "created_at": event.created_at,
        }


# ============================================================
# 17. USAGE TRACKING
# ============================================================

@dataclass
class UsageRecord:
    business_id: str

    counters: Dict[str, int] = field(
        default_factory=dict
    )

    updated_at: str = field(default_factory=utc_now)


class UsageManager:

    def __init__(self):
        self.usage: Dict[str, UsageRecord] = {}

    def increment(
        self,
        business_id: str,
        metric: str,
        amount: int = 1,
    ):

        record = self.usage.setdefault(
            business_id,
            UsageRecord(
                business_id=business_id
            ),
        )

        record.counters[metric] = (
            record.counters.get(metric, 0)
            + amount
        )

        record.updated_at = utc_now()

    def get(
        self,
        business_id: str,
    ) -> Dict[str, int]:

        record = self.usage.get(
            business_id
        )

        if not record:
            return {}

        return dict(record.counters)


# ============================================================
# 18. ONBOARDING WIZARD
# Business Setup حسب مجال العميل
# ============================================================

ONBOARDING_TEMPLATES = {

    "general": [
        ("business_name", "اسم النشاط أو الشركة؟"),
        ("business_type", "مجال النشاط؟"),
        ("description", "اشرح لي النشاط والخدمات أو المنتجات باختصار."),
        ("language", "ما اللغة الأساسية للعملاء؟"),
        ("currency", "ما العملة المستخدمة؟"),
    ],

    "handmade": [
        ("business_name", "اسم محل أو براند الإكسسوارات؟"),
        ("business_type", "ما نوع الإكسسوارات التي تبيعها؟"),
        ("products", "ما المنتجات الأساسية التي تقدمها؟"),
        ("customization", "هل يوجد تخصيص للمنتجات؟ وما أنواعه؟"),
        ("pricing", "هل الأسعار ثابتة أم تختلف حسب التخصيص؟"),
        ("delivery", "كيف يتم التوصيل؟"),
        ("payment", "ما طرق الدفع المتاحة؟"),
        ("customer_data", "ما البيانات التي تريد من الوكيل جمعها من العميل؟"),
        ("human_handoff", "متى يجب تحويل العميل إلى موظف؟"),
    ],

    "retail": [
        ("business_name", "اسم المتجر؟"),
        ("products", "ما المنتجات الأساسية؟"),
        ("pricing", "كيف يتم تحديد الأسعار؟"),
        ("inventory", "كيف يتم معرفة التوفر والمخزون؟"),
        ("delivery", "ما طرق التوصيل؟"),
        ("payment", "ما طرق الدفع؟"),
        ("human_handoff", "متى يتم تحويل العميل لموظف؟"),
    ],

    "restaurant": [
        ("business_name", "اسم المطعم؟"),
        ("menu", "ما أنواع الأطعمة أو المشروبات التي تقدمها؟"),
        ("delivery", "ما مناطق التوصيل؟"),
        ("payment", "ما طرق الدفع؟"),
        ("working_hours", "ما مواعيد العمل؟"),
        ("human_handoff", "متى يحتاج العميل للتحدث مع موظف؟"),
    ],

    "real_estate": [
        ("business_name", "اسم الشركة العقارية؟"),
        ("property_types", "ما أنواع العقارات التي تقدمونها؟"),
        ("areas", "ما المناطق التي تعملون بها؟"),
        ("budget", "كيف تريدون جمع ميزانية العميل؟"),
        ("payment", "ما أنظمة الدفع المتاحة؟"),
        ("viewing", "كيف يتم ترتيب معاينة العقار؟"),
        ("human_handoff", "متى يتم تحويل العميل لموظف؟"),
    ],

    "services": [
        ("business_name", "اسم الشركة أو مقدم الخدمة؟"),
        ("services", "ما الخدمات التي تقدمونها؟"),
        ("pricing", "كيف يتم تحديد الأسعار؟"),
        ("booking", "كيف يتم حجز الخدمة؟"),
        ("payment", "ما طرق الدفع؟"),
        ("human_handoff", "متى يتم تحويل العميل لموظف؟"),
    ],
}


@dataclass
class OnboardingState:
    business_id: str

    business_type: str

    questions: List[str] = field(
        default_factory=list
    )

    current_index: int = 0

    answers: Dict[str, Any] = field(
        default_factory=dict
    )

    completed: bool = False

    started_at: str = field(default_factory=utc_now)
    completed_at: str = ""


class OnboardingManager:

    def __init__(self):
        self.sessions: Dict[
            str,
            OnboardingState
        ] = {}

    def start(
        self,
        business_id: str,
        business_type: str,
    ) -> OnboardingState:

        template = ONBOARDING_TEMPLATES.get(
            business_type,
            ONBOARDING_TEMPLATES["general"]
        )

        question_keys = [
            key
            for key, _ in template
        ]

        state = OnboardingState(
            business_id=business_id,
            business_type=business_type,
            questions=question_keys,
        )

        self.sessions[business_id] = state

        return state

    def get_current_question(
        self,
        business_id: str,
    ) -> Optional[Dict[str, str]]:

        state = self.sessions.get(
            business_id
        )

        if not state or state.completed:
            return None

        template = ONBOARDING_TEMPLATES.get(
            state.business_type,
            ONBOARDING_TEMPLATES["general"]
        )

        if state.current_index >= len(template):
            return None

        key, question = template[
            state.current_index
        ]

        return {
            "key": key,
            "question": question,
        }

    def answer(
        self,
        business_id: str,
        answer: Any,
    ) -> Dict[str, Any]:

        state = self.sessions.get(
            business_id
        )

        if not state:
            raise ValueError(
                "Onboarding لم يبدأ"
            )

        if state.completed:
            return {
                "completed": True,
                "next_question": None,
            }

        current = self.get_current_question(
            business_id
        )

        if not current:
            state.completed = True
            state.completed_at = utc_now()

            return {
                "completed": True,
                "next_question": None,
            }

        state.answers[
            current["key"]
        ] = answer

        state.current_index += 1

        next_question = self.get_current_question(
            business_id
        )

        if not next_question:

            state.completed = True
            state.completed_at = utc_now()

        return {
            "completed": state.completed,
            "saved": {
                current["key"]: answer
            },
            "next_question": next_question,
        }


# ============================================================
# 19. DATABASE ABSTRACTION
# Foundation فقط
#
# حاليًا البيانات في الذاكرة.
# بعدين يمكن تركيب PostgreSQL / MySQL / MongoDB إلخ.
# ============================================================

class DataStore:

    def save(
        self,
        collection: str,
        object_id: str,
        data: Dict[str, Any],
    ):
        raise NotImplementedError

    def get(
        self,
        collection: str,
        object_id: str,
    ):
        raise NotImplementedError

    def list(
        self,
        collection: str,
    ):
        raise NotImplementedError


class SQLiteDataStore(DataStore):
    """تخزين دائم لحالة الـCore داخل SQLite."""

    def __init__(self, database: Optional[Database] = None):
        self.database = database or Database()
        self._initialize_state_table()

    def _initialize_state_table(self):
        self.database.execute("""
            CREATE TABLE IF NOT EXISTS core_state (
                collection TEXT NOT NULL,
                object_id TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (collection, object_id)
            )
        """)

    def save(self, collection: str, object_id: str, data: Dict[str, Any]):
        payload = json.dumps(data, ensure_ascii=False)
        self.database.execute(
            """
            INSERT INTO core_state (collection, object_id, data, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(collection, object_id) DO UPDATE SET
                data = excluded.data,
                updated_at = excluded.updated_at
            """,
            (collection, object_id, payload, utc_now()),
        )

    def get(self, collection: str, object_id: str):
        row = self.database.fetch_one(
            "SELECT data FROM core_state WHERE collection = ? AND object_id = ?",
            (collection, object_id),
        )
        if not row:
            return None
        return json.loads(row["data"])

    def list(self, collection: str):
        rows = self.database.fetch_all(
            "SELECT data FROM core_state WHERE collection = ? ORDER BY updated_at",
            (collection,),
        )
        return [json.loads(row["data"]) for row in rows]


class InMemoryDataStore(DataStore):

    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}

    def save(self, collection: str, object_id: str, data: Dict[str, Any]):
        self.data.setdefault(collection, {})[object_id] = deep_copy(data)

    def get(self, collection: str, object_id: str):
        return deep_copy(self.data.get(collection, {}).get(object_id))

    def list(self, collection: str):
        return deep_copy(list(self.data.get(collection, {}).values()))


# ============================================================
# 20. BACKGROUND JOB FOUNDATION
# تجهيز للـFollow-up / Reports / Automation
# ============================================================

@dataclass
class BackgroundJob:
    job_id: str
    business_id: str

    job_type: str

    payload: Dict[str, Any] = field(
        default_factory=dict
    )

    status: str = "pending"

    created_at: str = field(default_factory=utc_now)


class JobManager:

    def __init__(self):
        self.jobs: Dict[str, BackgroundJob] = {}

    def create(
        self,
        business_id: str,
        job_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> BackgroundJob:

        job = BackgroundJob(
            job_id=generate_id("job"),
            business_id=business_id,
            job_type=job_type,
            payload=payload or {},
        )

        self.jobs[job.job_id] = job

        return job

    def mark_completed(
        self,
        business_id: str,
        job_id: str,
    ):

        job = self.jobs.get(job_id)

        if not job:
            raise ValueError("Job غير موجود")

        if job.business_id != business_id:
            raise PermissionError(
                "لا يمكن الوصول إلى Job تخص Business آخر"
            )

        job.status = "completed"


# ============================================================
# 21. ANALYTICS FOUNDATION
# تعتمد على Events + Usage
# ============================================================

class AnalyticsManager:

    def __init__(
        self,
        event_manager: EventManager,
        usage_manager: UsageManager,
    ):

        self.event_manager = event_manager
        self.usage_manager = usage_manager

    def summary(
        self,
        business_id: str,
    ) -> Dict[str, Any]:

        business_events = [
            event
            for event in self.event_manager.events
            if event.business_id == business_id
        ]

        return {
            "business_id": business_id,
            "events_count": len(business_events),
            "usage": self.usage_manager.get(
                business_id
            ),
        }


# ============================================================
# 22. FUTURE ROADMAP
# حاجات مؤجلة ولكن معماريًا مجهزين لها مكان
# ============================================================

FUTURE_ROADMAP = [

    "subscription_and_billing",
    "advanced_dashboard",
    "affiliate_system",
    "advanced_optimization_learning",
    "vector_database",
    "semantic_search",
    "advanced_customer_support",
    "advanced_security_hardening",
    "advanced_multilingual",
    "production_queue_workers",
    "large_scale_database",
    "advanced_cloud_deployment",
    "production_backup_recovery",
]


# ============================================================
# 23. AIM CORE
# المنسق الرئيسي
# ============================================================

class AIMCore:

    def __init__(
        self,
        business_id: Optional[str] = None,
        business_name: str = "Default Business",
        business_type: str = "general",
    ):
        self.business_manager = BusinessManager()
        self.permission_manager = PermissionManager()
        self.customer_manager = CustomerManager()
        self.media_manager = MediaManager()
        self.conversation_manager = ConversationManager()
        self.catalog_manager = CatalogManager()
        self.order_manager = OrderManager()
        self.lead_manager = LeadManager()
        self.event_manager = EventManager()
        self.integration_manager = IntegrationManager()
        self.custom_field_manager = CustomFieldManager()
        self.audit_manager = AuditManager()
        self.api_manager = APIManager()
        self.usage_manager = UsageManager()
        self.onboarding_manager = OnboardingManager()
        self.data_store = SQLiteDataStore()
        self.job_manager = JobManager()
        self.analytics_manager = AnalyticsManager(self.event_manager, self.usage_manager)
        self.feature_manager = FeatureManager()

        requested_business_id = business_id
        saved_state = None
        if requested_business_id:
            saved_state = self.data_store.get("aim_core", requested_business_id)
        else:
            saved_state = self.data_store.get("aim_core", "default")

        if saved_state:
            self._restore_persistent_state(saved_state)
            return

        self.business = self.business_manager.create_business(
            name=business_name,
            business_type=business_type,
            business_id=business_id,
        )
        self.business_id = self.business.business_id

        self.system_user = self.permission_manager.add_user(
            business_id=self.business_id,
            name="AI Agent",
            role="owner",
        )
        self.customer = self.customer_manager.create_customer(
            business_id=self.business_id
        )
        self.customer_id = self.customer.customer_id
        self.session = self.conversation_manager.create_session(
            business_id=self.business_id,
            customer_id=self.customer_id,
            channel="web",
        )
        self.conversation_id = self.session.conversation_id
        self.customer_data = self.customer.data
        self.shown_items = self.session.shown_items
        self.conversation_history = []
        self._persist_state()

    def _build_persistent_state(self) -> Dict[str, Any]:
        return {
            "businesses": [asdict(x) for x in self.business_manager.businesses.values()],
            "users": [asdict(x) for x in self.permission_manager.users.values()],
            "customers": [asdict(x) for x in self.customer_manager.customers.values()],
            "media": [asdict(x) for x in self.media_manager.media.values()],
            "conversations": [asdict(x) for x in self.conversation_manager.sessions.values()],
            "catalog_items": [asdict(x) for x in self.catalog_manager.items.values()],
            "orders": [asdict(x) for x in self.order_manager.orders.values()],
            "leads": [asdict(x) for x in self.lead_manager.leads.values()],
            "events": [asdict(x) for x in self.event_manager.events],
            "integrations": [asdict(x) for x in self.integration_manager.integrations.values()],
            "custom_schemas": deep_copy(self.custom_field_manager.schemas),
            "custom_values": deep_copy(self.custom_field_manager.values),
            "audits": [asdict(x) for x in self.audit_manager.entries],
            "webhooks": [asdict(x) for x in self.api_manager.webhooks.values()],
            "usage": [asdict(x) for x in self.usage_manager.usage.values()],
            "onboarding": [asdict(x) for x in self.onboarding_manager.sessions.values()],
            "jobs": [asdict(x) for x in self.job_manager.jobs.values()],
            "business_id": self.business_id,
            "system_user_id": self.system_user.user_id,
            "customer_id": self.customer_id,
            "conversation_id": self.conversation_id,
            "conversation_history": deep_copy(self.conversation_history),
        }

    def _persist_state(self):
        self.data_store.save("aim_core", self.business_id, self._build_persistent_state())
        if self.business_id != "default":
            self.data_store.save("aim_core", "default", self._build_persistent_state())

    def save_state(self):
        self._persist_state()

    def _restore_persistent_state(self, state: Dict[str, Any]):
        for raw in state.get("businesses", []):
            obj = Business(**raw)
            self.business_manager.businesses[obj.business_id] = obj
        for raw in state.get("users", []):
            obj = User(**raw)
            self.permission_manager.users[obj.user_id] = obj
        for raw in state.get("customers", []):
            obj = Customer(**raw)
            self.customer_manager.customers[obj.customer_id] = obj
        for raw in state.get("media", []):
            obj = MediaObject(**raw)
            self.media_manager.media[obj.media_id] = obj
        for raw in state.get("conversations", []):
            raw = dict(raw)
            raw["messages"] = [Message(**m) for m in raw.get("messages", [])]
            obj = ConversationSession(**raw)
            self.conversation_manager.sessions[obj.conversation_id] = obj
        for raw in state.get("catalog_items", []):
            obj = CatalogItem(**raw)
            self.catalog_manager.items[obj.item_id] = obj
        for raw in state.get("orders", []):
            raw = dict(raw)
            raw["versions"] = [OrderVersion(**v) for v in raw.get("versions", [])]
            obj = Order(**raw)
            self.order_manager.orders[obj.order_id] = obj
        for raw in state.get("leads", []):
            obj = Lead(**raw)
            self.lead_manager.leads[obj.lead_id] = obj
        self.event_manager.events = [Event(**x) for x in state.get("events", [])]
        for raw in state.get("integrations", []):
            obj = Integration(**raw)
            self.integration_manager.integrations[obj.integration_id] = obj
        self.custom_field_manager.schemas = deep_copy(state.get("custom_schemas", {}))
        self.custom_field_manager.values = deep_copy(state.get("custom_values", {}))
        self.audit_manager.entries = [AuditEntry(**x) for x in state.get("audits", [])]
        for raw in state.get("webhooks", []):
            obj = Webhook(**raw)
            self.api_manager.webhooks[obj.webhook_id] = obj
        for raw in state.get("usage", []):
            obj = UsageRecord(**raw)
            self.usage_manager.usage[obj.business_id] = obj
        for raw in state.get("onboarding", []):
            obj = OnboardingState(**raw)
            self.onboarding_manager.sessions[obj.business_id] = obj
        for raw in state.get("jobs", []):
            obj = BackgroundJob(**raw)
            self.job_manager.jobs[obj.job_id] = obj

        self.business_id = state["business_id"]
        self.business = self.business_manager.businesses[self.business_id]
        self.system_user = self.permission_manager.users[state["system_user_id"]]
        self.customer_id = state["customer_id"]
        self.customer = self.customer_manager.customers[self.customer_id]
        self.conversation_id = state["conversation_id"]
        self.session = self.conversation_manager.sessions[self.conversation_id]
        self.customer_data = self.customer.data
        self.shown_items = self.session.shown_items
        self.conversation_history = deep_copy(state.get("conversation_history", []))

    # ========================================================
    # FEATURE FLAGS
    # ========================================================

    def is_feature_enabled(
        self,
        feature: str,
    ) -> bool:

        # Business-level override أولًا
        if feature in self.business.feature_flags:
            return bool(
                self.business.feature_flags[
                    feature
                ]
            )

        return self.feature_manager.is_enabled(
            feature
        )

    def enable_feature(
        self,
        feature: str,
    ):

        self.business.feature_flags[
            feature
        ] = True
        self._persist_state()

    def disable_feature(
        self,
        feature: str,
    ):

        self.business.feature_flags[
            feature
        ] = False
        self._persist_state()

    # ========================================================
    # CUSTOMER MEMORY
    # ========================================================

    def update_customer_data(
        self,
        data: Dict[str, Any],
    ):

        if not isinstance(data, dict):
            return

        self.customer_manager.update_customer(
            business_id=self.business_id,
            customer_id=self.customer_id,
            data=data,
        )

        # الحفاظ على نفس المرجع المستخدم في main.py
        self.customer_data = self.customer.data

        self.usage_manager.increment(
            self.business_id,
            "customer_data_updates",
        )

        self.event_manager.emit(
            business_id=self.business_id,
            event_type="customer.updated",
            payload={
                "customer_id": self.customer_id,
                "data": deep_copy(data),
            },
        )

        self.audit_manager.log(
            business_id=self.business_id,
            action="customer.update",
            resource_type="customer",
            resource_id=self.customer_id,
            details={
                "fields": list(data.keys())
            },
        )
        self._persist_state()

    # ========================================================
    # CONVERSATION
    # ========================================================

    def add_message(
        self,
        role: str,
        message: str,
        channel: Optional[str] = None,
        media: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        if channel and channel != self.session.channel:

            # إنشاء Session جديدة للقناة الجديدة
            self.session = (
                self.conversation_manager.create_session(
                    business_id=self.business_id,
                    customer_id=self.customer_id,
                    channel=channel,
                )
            )

            self.conversation_id = (
                self.session.conversation_id
            )

            self.shown_items = (
                self.session.shown_items
            )

        msg = self.conversation_manager.add_message(
            business_id=self.business_id,
            conversation_id=self.conversation_id,
            role=role,
            content=message,
            media=media,
            metadata=metadata,
        )

        self.conversation_history.append({
            "message_id": msg.message_id,
            "role": role,
            "message": message,
            "channel": msg.channel,
            "created_at": msg.created_at,
        })

        self.usage_manager.increment(
            self.business_id,
            "messages",
        )

        self.event_manager.emit(
            business_id=self.business_id,
            event_type="message.created",
            payload={
                "message_id": msg.message_id,
                "conversation_id": self.conversation_id,
                "customer_id": self.customer_id,
                "role": role,
            },
        )

        self._persist_state()
        return msg

    # ========================================================
    # SHOWN ITEMS
    # ========================================================

    def mark_item_as_shown(
        self,
        item_id: str,
    ):

        if item_id not in self.shown_items:

            self.shown_items.append(
                item_id
            )

        self.session.shown_items = (
            self.shown_items
        )
        self._persist_state()

    def filter_unshown_items(
        self,
        items: List[Dict[str, Any]],
        id_field: str = "id",
    ) -> List[Dict[str, Any]]:

        result = []

        for item in items:

            item_id = item.get(
                id_field
            )

            if item_id not in self.shown_items:

                result.append(item)

        return result

    # ========================================================
    # MEDIA
    # ========================================================

    def create_media(
        self,
        media_type: str,
        **kwargs,
    ) -> MediaObject:

        media = self.media_manager.create_media(
            media_type=media_type,
            **kwargs,
        )

        self.usage_manager.increment(
            self.business_id,
            f"media_{media_type}",
        )
        self._persist_state()

        return media

    # ========================================================
    # CATALOG
    # ========================================================

    def add_catalog_item(
        self,
        name: str,
        item_type: str = "product",
        price: Optional[float] = None,
        data: Optional[Dict[str, Any]] = None,
        item_id: Optional[str] = None,
    ) -> CatalogItem:

        item = self.catalog_manager.add_item(
            business_id=self.business_id,
            name=name,
            item_type=item_type,
            price=price,
            data=data,
            item_id=item_id,
        )

        self.event_manager.emit(
            business_id=self.business_id,
            event_type="catalog.item_created",
            payload={
                "item_id": item.item_id
            },
        )
        self._persist_state()

        return item

    # ========================================================
    # ORDER
    # ========================================================

    def create_order(
        self,
        data: Optional[Dict[str, Any]] = None,
    ) -> Order:

        order = self.order_manager.create_order(
            business_id=self.business_id,
            customer_id=self.customer_id,
            data=data,
        )

        self.usage_manager.increment(
            self.business_id,
            "orders_created",
        )

        self.event_manager.emit(
            business_id=self.business_id,
            event_type="order.created",
            payload={
                "order_id": order.order_id
            },
        )
        self._persist_state()

        return order

    def update_order(
        self,
        order_id: str,
        changes: Dict[str, Any],
        changed_by: str = "system",
    ) -> Order:

        order = self.order_manager.update_order(
            business_id=self.business_id,
            order_id=order_id,
            changes=changes,
            changed_by=changed_by,
        )

        self.event_manager.emit(
            business_id=self.business_id,
            event_type="order.updated",
            payload={
                "order_id": order_id,
                "version": order.current_version,
            },
            actor_id=changed_by,
        )
        self._persist_state()

        return order

    # ========================================================
    # LEAD
    # ========================================================

    def create_or_update_lead(
        self,
        status: str,
        interest_score: int,
        data: Optional[Dict[str, Any]] = None,
    ) -> Lead:

        lead = self.lead_manager.create_or_update_lead(
            business_id=self.business_id,
            customer_id=self.customer_id,
            status=status,
            interest_score=interest_score,
            data=data,
        )

        self.usage_manager.increment(
            self.business_id,
            "leads",
        )

        self.event_manager.emit(
            business_id=self.business_id,
            event_type="lead.updated",
            payload={
                "lead_id": lead.lead_id,
                "status": status,
                "interest_score": interest_score,
            },
        )
        self._persist_state()

        return lead

    # ========================================================
    # HUMAN HANDOFF
    # ========================================================

    def request_human_handoff(
        self,
        reason: str = "",
    ):

        self.customer_manager.set_status(
            business_id=self.business_id,
            customer_id=self.customer_id,
            status="human_handoff",
        )

        self.event_manager.emit(
            business_id=self.business_id,
            event_type="human_handoff.requested",
            payload={
                "customer_id": self.customer_id,
                "conversation_id": self.conversation_id,
                "reason": reason,
            },
        )
        self._persist_state()

    # ========================================================
    # CUSTOM FIELDS
    # ========================================================

    def define_custom_field(
        self,
        field_name: str,
        field_type: str = "text",
        required: bool = False,
    ):

        self.custom_field_manager.define_field(
            business_id=self.business_id,
            field_name=field_name,
            field_type=field_type,
            required=required,
        )

        self.business.custom_field_definitions[
            field_name
        ] = {
            "name": field_name,
            "type": field_type,
            "required": required,
        }
        self._persist_state()

    def set_customer_custom_field(
        self,
        field_name: str,
        value: Any,
    ):

        self.custom_field_manager.set_value(
            business_id=self.business_id,
            entity_id=self.customer_id,
            field_name=field_name,
            value=value,
        )

        self.customer.custom_fields[
            field_name
        ] = value
        self._persist_state()

    # ========================================================
    # ONBOARDING
    # ========================================================

    def start_onboarding(
        self,
        business_type: Optional[str] = None,
    ):

        business_type = (
            business_type
            or self.business.business_type
        )

        state = self.onboarding_manager.start(
            business_id=self.business_id,
            business_type=business_type,
        )

        result = self.onboarding_manager.get_current_question(
            self.business_id
        )
        self._persist_state()
        return result

    def answer_onboarding(
        self,
        answer: Any,
    ) -> Dict[str, Any]:

        result = self.onboarding_manager.answer(
            business_id=self.business_id,
            answer=answer,
        )

        if result.get("completed"):

            state = self.onboarding_manager.sessions[
                self.business_id
            ]

            self.business.onboarding_data = (
                deep_copy(state.answers)
            )

            self.business.config.update(
                deep_copy(state.answers)
            )

            self.event_manager.emit(
                business_id=self.business_id,
                event_type="business.onboarding_completed",
                payload={
                    "answers": deep_copy(
                        state.answers
                    )
                },
            )

        self._persist_state()
        return result

    # ========================================================
    # INTEGRATIONS
    # ========================================================

    def register_integration(
        self,
        name: str,
        integration_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Integration:

        result = self.integration_manager.register(
            business_id=self.business_id,
            name=name,
            integration_type=integration_type,
            config=config,
        )
        self._persist_state()
        return result

    # ========================================================
    # WEBHOOK
    # ========================================================

    def register_webhook(
        self,
        url: str,
        event_types: List[str],
    ) -> Webhook:

        result = self.api_manager.register_webhook(
            business_id=self.business_id,
            url=url,
            event_types=event_types,
        )
        self._persist_state()
        return result

    # ========================================================
    # USAGE
    # ========================================================

    def get_usage(self) -> Dict[str, int]:

        return self.usage_manager.get(
            self.business_id
        )

    # ========================================================
    # ANALYTICS
    # ========================================================

    def get_analytics_summary(
        self,
    ) -> Dict[str, Any]:

        return self.analytics_manager.summary(
            self.business_id
        )

    # ========================================================
    # BACKGROUND JOB
    # ========================================================

    def create_background_job(
        self,
        job_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> BackgroundJob:

        result = self.job_manager.create(
            business_id=self.business_id,
            job_type=job_type,
            payload=payload,
        )
        self._persist_state()
        return result

    # ========================================================
    # BUSINESS CONFIG
    # ========================================================

    def update_business_config(
        self,
        config: Dict[str, Any],
    ):

        self.business_manager.update_config(
            business_id=self.business_id,
            config=config,
        )
        self._persist_state()

    # ========================================================
    # SERIALIZATION
    # تحويل حالة الـCore إلى JSON-friendly object
    # ========================================================

    def export_state(self) -> Dict[str, Any]:

        return {
            "business": asdict(
                self.business
            ),

            "customer": asdict(
                self.customer
            ),

            "media": [asdict(x) for x in self.media_manager.media.values()],

            "conversation": asdict(
                self.session
            ),

            "usage": self.get_usage(),

            "features": dict(
                self.business.feature_flags
            ),

            "future_roadmap": list(
                FUTURE_ROADMAP
            ),
        }

    def export_json(self) -> str:

        return json.dumps(
            self.export_state(),
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# 24. LOCAL TEST
# لا يستخدم Gemini
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("🧠 AIM CORE LOCAL TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # إنشاء Business
    # --------------------------------------------------------

    core = AIMCore(
        business_name="متجر إكسسوارات هاند ميد",
        business_type="handmade",
    )

    print("\n✅ Business:")
    print(core.business.business_id)
    print(core.business.name)

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    core.update_customer_data({
        "name": "معتز",
        "phone": "01000000000",
        "favorite_color": "ذهبي",
    })

    print("\n✅ Customer:")
    print(core.customer_data)

    # --------------------------------------------------------
    # Conversation
    # --------------------------------------------------------

    core.add_message(
        "customer",
        "عايز إسورة كلاسيك"
    )

    core.add_message(
        "agent",
        "أكيد، إسورة كلاسيك متاحة."
    )

    print("\n✅ Conversation:")
    print(
        "عدد الرسائل:",
        len(core.conversation_history)
    )

    # --------------------------------------------------------
    # Shown Items
    # --------------------------------------------------------

    core.mark_item_as_shown("P002")

    products = [
        {
            "product_id": "P001",
            "name": "إسورة سارة",
        },
        {
            "product_id": "P002",
            "name": "إسورة كلاسيك",
        },
        {
            "product_id": "P003",
            "name": "سلسلة هاند ميد",
        },
    ]

    unshown = core.filter_unshown_items(
        products,
        id_field="product_id",
    )

    print("\n✅ Shown Items:")
    print(core.shown_items)

    print("\nالعناصر التي لم يتم عرضها:")
    print(unshown)

    # --------------------------------------------------------
    # Media
    # --------------------------------------------------------

    image = core.create_media(
        "image",
        url="customer_image.jpg",
        mime_type="image/jpeg",
    )

    core.media_manager.add_analysis(
        image,
        {
            "detected_type": "bracelet",
            "confidence": 0.91,
        },
    )

    print("\n✅ Image Media:")
    print(asdict(image))

    # --------------------------------------------------------
    # Order
    # --------------------------------------------------------

    order = core.create_order({
        "product_id": "P002",
        "quantity": 1,
        "color": "ذهبي",
    })

    core.update_order(
        order.order_id,
        {
            "quantity": 2,
        },
        changed_by="customer",
    )

    print("\n✅ Order:")
    print(
        "Order ID:",
        order.order_id
    )

    print(
        "Order Version:",
        order.current_version
    )

    print(
        "Version History:",
        len(order.versions)
    )

    # --------------------------------------------------------
    # Lead
    # --------------------------------------------------------

    lead = core.create_or_update_lead(
        status="qualified",
        interest_score=90,
        data={
            "product": "إسورة كلاسيك",
        },
    )

    print("\n✅ Lead:")
    print(asdict(lead))

    # --------------------------------------------------------
    # Human Handoff
    # --------------------------------------------------------

    core.request_human_handoff(
        "العميل طلب التحدث مع موظف"
    )

    print("\n✅ Human Handoff:")
    print(core.customer.status)

    # --------------------------------------------------------
    # Feature Flag
    # --------------------------------------------------------

    core.disable_feature(
        "voice_transcription"
    )

    print("\n✅ Feature Flag:")
    print(
        "voice_transcription =",
        core.is_feature_enabled(
            "voice_transcription"
        )
    )

    core.enable_feature(
        "voice_transcription"
    )

    print(
        "voice_transcription =",
        core.is_feature_enabled(
            "voice_transcription"
        )
    )

    # --------------------------------------------------------
    # Custom Field
    # --------------------------------------------------------

    core.define_custom_field(
        "customer_size",
        field_type="text",
    )

    core.set_customer_custom_field(
        "customer_size",
        "متوسط",
    )

    print("\n✅ Custom Field:")
    print(
        core.customer.custom_fields
    )

    # --------------------------------------------------------
    # Onboarding
    # --------------------------------------------------------

    question = core.start_onboarding(
        "handmade"
    )

    print("\n✅ Onboarding first question:")
    print(question)

    # --------------------------------------------------------
    # Integration
    # --------------------------------------------------------

    whatsapp = core.register_integration(
        name="WhatsApp",
        integration_type="whatsapp",
    )

    print("\n✅ Integration:")
    print(asdict(whatsapp))

    # --------------------------------------------------------
    # Webhook
    # --------------------------------------------------------

    webhook = core.register_webhook(
        url="https://example.com/webhook",
        event_types=[
            "message.created",
            "lead.updated",
            "order.updated",
        ],
    )

    print("\n✅ Webhook:")
    print(asdict(webhook))

    # --------------------------------------------------------
    # Background Job
    # --------------------------------------------------------

    job = core.create_background_job(
        "follow_up",
        {
            "customer_id": core.customer_id,
        },
    )

    print("\n✅ Background Job:")
    print(asdict(job))

    # --------------------------------------------------------
    # Usage
    # --------------------------------------------------------

    print("\n✅ Usage:")
    print(core.get_usage())

    # --------------------------------------------------------
    # Analytics
    # --------------------------------------------------------

    print("\n✅ Analytics:")
    print(core.get_analytics_summary())

    # --------------------------------------------------------
    # Final Export
    # --------------------------------------------------------

    print("\n✅ Export Test:")
    exported = core.export_state()

    print(
        "Business ID:",
        exported["business"]["business_id"]
    )

    print(
        "Customer ID:",
        exported["customer"]["customer_id"]
    )

    print(
        "Conversation ID:",
        exported["conversation"][
            "conversation_id"
        ]
    )

    print("\n" + "=" * 60)
    print("🎉 AIM CORE TEST FINISHED")
    print("=" * 60)