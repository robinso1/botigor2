from sqlalchemy.orm import Session
from app.models import User, Request, RequestAssignment, RequestStatus
from app.config import settings
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class RequestDistributor:
    def __init__(self, db: Session):
        self.db = db
    
    def get_eligible_users(self, request: Request) -> list[User]:
        """Получить список подходящих пользователей для заявки"""
        query = self.db.query(User).filter(
            User.is_active == True,
            User.categories.any(id=request.category_id),
            User.cities.any(id=request.city_id)
        )
        return query.all()
    
    def distribute_request(self, request: Request) -> list[RequestAssignment]:
        """Распределить заявку между пользователями"""
        if request.send_count >= settings.MAX_REQUEST_SENDS:
            request.status = RequestStatus.INACTIVE
            self.db.commit()
            return []
        
        # Получаем подходящих пользователей
        eligible_users = self.get_eligible_users(request)
        if not eligible_users:
            logger.warning(f"No eligible users found for request {request.id}")
            return []
        
        # Проверяем, не отправлялась ли заявка пользователям недавно
        cutoff_time = datetime.utcnow() - timedelta(hours=settings.REQUEST_INTERVAL_HOURS)
        recent_assignments = self.db.query(RequestAssignment).filter(
            RequestAssignment.request_id == request.id,
            RequestAssignment.assigned_at > cutoff_time
        ).all()
        
        if recent_assignments:
            logger.info(f"Request {request.id} was recently distributed")
            return []
        
        # Выбираем случайных пользователей
        selected_users = random.sample(
            eligible_users,
            min(len(eligible_users), settings.MAX_USERS_PER_REQUEST)
        )
        
        # Создаем назначения
        assignments = []
        for user in selected_users:
            assignment = RequestAssignment(
                request_id=request.id,
                user_id=user.id,
                status=RequestStatus.NEW
            )
            self.db.add(assignment)
            assignments.append(assignment)
        
        # Обновляем счетчик отправок
        request.send_count += 1
        self.db.commit()
        
        return assignments
    
    def distribute_pending_requests(self) -> int:
        """Распределить все ожидающие заявки"""
        pending_requests = self.db.query(Request).filter(
            Request.status == RequestStatus.NEW,
            Request.send_count < settings.MAX_REQUEST_SENDS
        ).all()
        
        distributed_count = 0
        for request in pending_requests:
            assignments = self.distribute_request(request)
            if assignments:
                distributed_count += 1
        
        return distributed_count 