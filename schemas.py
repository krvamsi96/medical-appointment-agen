from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Literal
from datetime import datetime, date, time


class PatientInfo(BaseModel):
    """Patient information for appointment booking"""
    name: str = Field(..., description="Patient's full name")
    email: EmailStr = Field(..., description="Patient's email address")
    phone: str = Field(..., description="Patient's phone number")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Remove common separators
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v


class AppointmentType(BaseModel):
    """Appointment type configuration"""
    type_name: Literal["general_consultation", "follow_up", "physical_exam", "specialist_consultation"]
    duration_minutes: int
    description: str


class TimeSlot(BaseModel):
    """Available time slot"""
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    available: bool = True


class AppointmentRequest(BaseModel):
    """Appointment booking request"""
    appointment_type: Literal["general_consultation", "follow_up", "physical_exam", "specialist_consultation"]
    appointment_date: str = Field(..., description="Date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM format")
    patient: PatientInfo
    reason: str = Field(..., description="Reason for visit")


class AppointmentResponse(BaseModel):
    """Appointment booking response"""
    booking_id: str
    status: Literal["confirmed", "pending", "failed"]
    confirmation_code: str
    appointment_type: str
    date: str
    start_time: str
    end_time: str
    patient_name: str
    patient_email: str
    reason: str
    created_at: str


class AvailabilityRequest(BaseModel):
    """Request for checking availability"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    appointment_type: Literal["general_consultation", "follow_up", "physical_exam", "specialist_consultation"]


class AvailabilityResponse(BaseModel):
    """Response with available time slots"""
    date: str
    appointment_type: str
    available_slots: List[TimeSlot]
    total_slots: int


class ChatMessage(BaseModel):
    """Chat message model"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None


class AgentState(BaseModel):
    """Agent conversation state"""
    conversation_id: str
    phase: Literal["greeting", "understanding", "scheduling", "confirming", "completed", "faq"]
    appointment_data: Optional[dict] = None
    patient_info: Optional[PatientInfo] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    appointment_type: Optional[str] = None
    reason_for_visit: Optional[str] = None


# Appointment type configurations
APPOINTMENT_TYPES = {
    "general_consultation": {
        "duration": 30,
        "description": "Standard consultation for new health concerns, chronic condition management, or general check-ups"
    },
    "follow_up": {
        "duration": 15,
        "description": "Brief follow-up for ongoing treatment, test result review, or medication adjustment"
    },
    "physical_exam": {
        "duration": 45,
        "description": "Comprehensive annual physical examination including health screening and preventive care"
    },
    "specialist_consultation": {
        "duration": 60,
        "description": "Extended consultation for complex conditions requiring specialist expertise"
    }
}


# Business configuration
class BusinessConfig(BaseModel):
    """Clinic business configuration"""
    name: str = "HealthCare Plus Clinic"
    phone: str = "+1-555-123-4567"
    email: str = "info@healthcareplus.com"
    timezone: str = "America/New_York"
    business_hours: dict = {
        "start": "09:00",
        "end": "17:00",
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    }
