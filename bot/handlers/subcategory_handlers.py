"""
Обработчики для работы с подкатегориями
"""
import logging
from typing import List, Dict, Any, Optional

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.setup import get_session
from bot.models import User, Category, SubCategory
from bot.services.user_service import UserService

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер
router = Router()

class SubCategoryStates(StatesGroup):
    """Состояния для работы с подкатегориями"""
    selecting_category = State()
    selecting_subcategory = State()
    entering_value = State()


async def get_subcategories_by_category(category_id: int) -> List[Dict[str, Any]]:
    """Получение подкатегорий по ID категории"""
    with get_session() as session:
        subcategories = session.query(SubCategory).filter(
            SubCategory.category_id == category_id,
            SubCategory.is_active == True
        ).all()
        
        result = []
        for subcategory in subcategories:
            result.append({
                "id": subcategory.id,
                "name": subcategory.name,
                "description": subcategory.description,
                "type": subcategory.type,
                "min_value": subcategory.min_value,
                "max_value": subcategory.max_value
            })
        
        return result


async def get_user_subcategories(user_id: int) -> List[Dict[str, Any]]:
    """Получение подкатегорий пользователя"""
    with get_session() as session:
        user_service = UserService(session)
        db_user = user_service.get_user_by_telegram_id(user_id)
        
        if not db_user:
            return []
        
        result = []
        for subcategory in db_user.subcategories:
            result.append({
                "id": subcategory.id,
                "name": subcategory.name,
                "category_id": subcategory.category_id,
                "category_name": subcategory.category.name if subcategory.category else "Неизвестно",
                "type": subcategory.type,
                "value": None  # Здесь можно добавить значение, если оно хранится
            })
        
        return result


@router.message(F.text == "🔍 Выбрать подкатегории")
async def select_subcategories_start(message: types.Message, state: FSMContext):
    """Начало процесса выбора подкатегорий"""
    logger.info(f"Пользователь {message.from_user.id} начал выбор подкатегорий")
    
    # Получаем категории пользователя
    with get_session() as session:
        user_service = UserService(session)
        db_user = user_service.get_user_by_telegram_id(message.from_user.id)
        
        if not db_user:
            await message.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
            return
        
        # Получаем категории пользователя
        user_categories = db_user.categories
        
        if not user_categories:
            await message.answer(
                "У вас не выбрано ни одной категории. Пожалуйста, сначала выберите категории в разделе 'Мой профиль'."
            )
            return
        
        # Создаем клавиатуру с категориями
        keyboard = []
        for category in user_categories:
            keyboard.append([types.KeyboardButton(text=f"📂 {category.name}")])
        
        # Добавляем кнопку "Назад"
        keyboard.append([types.KeyboardButton(text="🔙 Вернуться в профиль")])
        
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        
        # Сохраняем состояние
        await state.set_state(SubCategoryStates.selecting_category)
        
        await message.answer(
            "Выберите категорию, для которой хотите настроить дополнительные критерии:",
            reply_markup=reply_markup
        )


@router.message(SubCategoryStates.selecting_category, F.text.startswith("📂 "))
async def select_category(message: types.Message, state: FSMContext):
    """Выбор категории для настройки подкатегорий"""
    category_name = message.text[2:].strip()
    logger.info(f"Пользователь {message.from_user.id} выбрал категорию {category_name}")
    
    # Получаем категорию
    with get_session() as session:
        category = session.query(Category).filter(
            Category.name == category_name,
            Category.is_active == True
        ).first()
        
        if not category:
            await message.answer(f"Категория '{category_name}' не найдена.")
            return
        
        # Получаем подкатегории для выбранной категории
        subcategories = session.query(SubCategory).filter(
            SubCategory.category_id == category.id,
            SubCategory.is_active == True
        ).all()
        
        if not subcategories:
            await message.answer(
                f"Для категории '{category_name}' нет доступных дополнительных критериев."
            )
            return
        
        # Получаем пользователя и его подкатегории
        user_service = UserService(session)
        db_user = user_service.get_user_by_telegram_id(message.from_user.id)
        user_subcategory_ids = [sc.id for sc in db_user.subcategories]
        
        # Сохраняем выбранную категорию в состоянии
        await state.update_data(selected_category_id=category.id, selected_category_name=category.name)
        
        # Создаем клавиатуру с подкатегориями
        keyboard = []
        for subcategory in subcategories:
            # Добавляем маркер выбранной подкатегории
            status = "✅" if subcategory.id in user_subcategory_ids else "❌"
            keyboard.append([types.KeyboardButton(text=f"{status} {subcategory.name}")])
        
        # Добавляем кнопки "Готово" и "Назад"
        keyboard.append([types.KeyboardButton(text="✅ Готово")])
        keyboard.append([types.KeyboardButton(text="🔙 Назад к категориям")])
        
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        
        # Сохраняем состояние
        await state.set_state(SubCategoryStates.selecting_subcategory)
        
        await message.answer(
            f"Выберите дополнительные критерии для категории '{category_name}':\n\n"
            "❌ - критерий не выбран\n"
            "✅ - критерий выбран\n\n"
            "Нажимайте на критерии для выбора/отмены.\n"
            "После завершения выбора нажмите кнопку '✅ Готово'.",
            reply_markup=reply_markup
        )


@router.message(SubCategoryStates.selecting_subcategory, F.text.startswith(("✅ ", "❌ ")))
async def toggle_subcategory(message: types.Message, state: FSMContext):
    """Выбор/отмена подкатегории"""
    subcategory_name = message.text[2:].strip()
    is_selected = message.text.startswith("✅ ")
    
    logger.info(f"Пользователь {message.from_user.id} {'отменил' if is_selected else 'выбрал'} подкатегорию {subcategory_name}")
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    category_id = state_data.get("selected_category_id")
    category_name = state_data.get("selected_category_name")
    
    if not category_id:
        await message.answer("Ошибка: не выбрана категория. Пожалуйста, начните процесс заново.")
        await state.clear()
        return
    
    # Обновляем выбор подкатегории
    with get_session() as session:
        # Получаем подкатегорию
        subcategory = session.query(SubCategory).filter(
            SubCategory.name == subcategory_name,
            SubCategory.category_id == category_id,
            SubCategory.is_active == True
        ).first()
        
        if not subcategory:
            await message.answer(f"Критерий '{subcategory_name}' не найден.")
            return
        
        # Получаем пользователя
        user_service = UserService(session)
        db_user = user_service.get_user_by_telegram_id(message.from_user.id)
        
        if not db_user:
            await message.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
            return
        
        # Обновляем выбор подкатегории
        if is_selected:
            # Удаляем подкатегорию
            if subcategory in db_user.subcategories:
                db_user.subcategories.remove(subcategory)
                session.commit()
        else:
            # Добавляем подкатегорию
            if subcategory not in db_user.subcategories:
                db_user.subcategories.append(subcategory)
                session.commit()
        
        # Получаем обновленный список подкатегорий для категории
        subcategories = session.query(SubCategory).filter(
            SubCategory.category_id == category_id,
            SubCategory.is_active == True
        ).all()
        
        user_subcategory_ids = [sc.id for sc in db_user.subcategories]
        
        # Создаем клавиатуру с подкатегориями
        keyboard = []
        for sc in subcategories:
            # Добавляем маркер выбранной подкатегории
            status = "✅" if sc.id in user_subcategory_ids else "❌"
            keyboard.append([types.KeyboardButton(text=f"{status} {sc.name}")])
        
        # Добавляем кнопки "Готово" и "Назад"
        keyboard.append([types.KeyboardButton(text="✅ Готово")])
        keyboard.append([types.KeyboardButton(text="🔙 Назад к категориям")])
        
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        
        await message.answer(
            f"Критерий '{subcategory_name}' {'удален' if is_selected else 'добавлен'}.",
            reply_markup=reply_markup
        )


@router.message(SubCategoryStates.selecting_subcategory, F.text == "✅ Готово")
async def subcategory_selection_done(message: types.Message, state: FSMContext):
    """Завершение выбора подкатегорий"""
    logger.info(f"Пользователь {message.from_user.id} завершил выбор подкатегорий")
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    category_name = state_data.get("selected_category_name", "выбранной категории")
    
    # Очищаем состояние
    await state.clear()
    
    # Создаем клавиатуру для возврата в профиль
    keyboard = [
        [types.KeyboardButton(text="👤 Мой профиль")],
        [types.KeyboardButton(text="🔙 Вернуться в главное меню")]
    ]
    reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    
    await message.answer(
        f"Настройка дополнительных критериев для категории '{category_name}' завершена.",
        reply_markup=reply_markup
    )


@router.message(SubCategoryStates.selecting_subcategory, F.text == "🔙 Назад к категориям")
async def back_to_categories(message: types.Message, state: FSMContext):
    """Возврат к выбору категорий"""
    logger.info(f"Пользователь {message.from_user.id} вернулся к выбору категорий")
    
    # Очищаем данные о выбранной категории
    await state.update_data(selected_category_id=None, selected_category_name=None)
    
    # Получаем категории пользователя
    with get_session() as session:
        user_service = UserService(session)
        db_user = user_service.get_user_by_telegram_id(message.from_user.id)
        
        if not db_user:
            await message.answer("Пользователь не найден. Пожалуйста, используйте /start для регистрации.")
            return
        
        # Получаем категории пользователя
        user_categories = db_user.categories
        
        # Создаем клавиатуру с категориями
        keyboard = []
        for category in user_categories:
            keyboard.append([types.KeyboardButton(text=f"📂 {category.name}")])
        
        # Добавляем кнопку "Назад"
        keyboard.append([types.KeyboardButton(text="🔙 Вернуться в профиль")])
        
        reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        
        # Сохраняем состояние
        await state.set_state(SubCategoryStates.selecting_category)
        
        await message.answer(
            "Выберите категорию, для которой хотите настроить дополнительные критерии:",
            reply_markup=reply_markup
        )


@router.message(SubCategoryStates.selecting_category, F.text == "🔙 Вернуться в профиль")
async def back_to_profile(message: types.Message, state: FSMContext):
    """Возврат в профиль"""
    logger.info(f"Пользователь {message.from_user.id} вернулся в профиль")
    
    # Очищаем состояние
    await state.clear()
    
    # Создаем клавиатуру для профиля
    keyboard = [
        [types.KeyboardButton(text="👤 Мой профиль")],
        [types.KeyboardButton(text="🔙 Вернуться в главное меню")]
    ]
    reply_markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    
    await message.answer(
        "Вы вернулись в раздел профиля.",
        reply_markup=reply_markup
    ) 