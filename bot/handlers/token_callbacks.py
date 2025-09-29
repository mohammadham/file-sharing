#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Management Callbacks Router - مسیریابی callback های مدیریت توکن
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class TokenCallbacks:
    """مسیریابی callback های مربوط به مدیریت توکن"""
    
    def __init__(self, db, token_handlers_dict):
        """
        Args:
            db: دیتابیس منیجر
            token_handlers_dict: دیکشنری شامل تمام handler های توکن
        """
        self.db = db
        self.handlers = token_handlers_dict
    
    async def route_token_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """مسیریابی callback های توکن به handler مناسب"""
        try:
            # === Dashboard & Main Menu ===
            if callback_data in ['token_management', 'token_dashboard']:
                await self.handlers['dashboard'].show_token_dashboard(update, context)
            elif callback_data == 'manage_tokens':
                await self.handlers['dashboard'].show_manage_tokens_menu(update, context)
            elif callback_data == 'security_menu':
                await self.handlers['security_advanced'].show_security_main_menu(update, context)
            elif callback_data == 'reports_menu':
                await self.handlers['reports'].show_reports_menu(update, context)
            elif callback_data == 'cleanup_menu':
                await self.handlers['cleanup'].show_cleanup_menu(update, context)
            elif callback_data == 'users_menu':
                await self.handlers['users'].show_users_menu(update, context)
            
            # === Token CRUD Operations ===
            elif callback_data in ['generate_new_token', 'create_new_token']:
                await self.handlers['dashboard'].show_create_token_wizard(update, context)
            elif callback_data in ['view_all_tokens', 'list_all_tokens']:
                await self.handlers['dashboard'].show_token_list(update, context)
            elif callback_data.startswith('create_token_'):
                await self.handlers['dashboard'].process_token_creation(update, context)
            elif callback_data.startswith('confirm_new_token_'):
                await self.handlers['dashboard'].handle_confirm_new_token(update, context)
            elif callback_data.startswith('copy_token_'):
                await self.handlers['dashboard'].handle_copy_token(update, context)
            elif callback_data.startswith('token_details_'):
                await self.handlers['dashboard'].handle_token_details(update, context)
            
            # === Security Settings ===
            elif callback_data == 'token_security_settings':
                await self.handlers['security'].show_security_settings(update, context)
            elif callback_data == 'set_default_expiry':
                await self.handlers['security'].handle_set_default_expiry(update, context)
            elif callback_data == 'set_usage_limit':
                await self.handlers['security'].handle_set_usage_limit(update, context)
            elif callback_data == 'ip_restrictions':
                await self.handlers['security'].handle_ip_restrictions(update, context)
            elif callback_data == 'security_alerts':
                await self.handlers['security'].handle_security_alerts(update, context)
            elif callback_data.startswith('set_expiry_'):
                await self.handlers['security'].handle_set_expiry_action(update, context)
            
            # === Cleanup Operations ===
            elif callback_data == 'cleanup_tokens':
                await self.handlers['cleanup'].show_cleanup_options(update, context)
            elif callback_data.startswith('cleanup_'):
                await self.handlers['cleanup'].handle_cleanup_action(update, context)
            
            # === Deactivation Operations ===
            elif callback_data == 'deactivate_tokens':
                await self.handlers['security'].handle_deactivate_tokens(update, context)
            elif callback_data == 'set_token_expiry':
                await self.handlers['security'].handle_set_token_expiry(update, context)
            elif callback_data == 'deactivate_current_token':
                await self.handlers['security'].handle_deactivate_current_token(update, context)
            elif callback_data == 'deactivate_expired_tokens':
                await self.handlers['security'].handle_deactivate_expired_tokens(update, context)
            elif callback_data == 'deactivate_user_tokens':
                await self.handlers['users'].handle_deactivate_user_tokens(update, context)
            elif callback_data == 'deactivate_suspicious_tokens':
                await self.handlers['security'].handle_deactivate_suspicious_tokens(update, context)
            
            # === Reports & Statistics ===
            elif callback_data == 'token_manage_permissions':
                await self.handlers['dashboard'].show_permissions_manager(update, context)
            elif callback_data == 'token_usage_report':
                await self.handlers['reports'].show_usage_report(update, context)
            elif callback_data == 'detailed_token_stats':
                await self.handlers['reports'].handle_detailed_token_stats(update, context)
            elif callback_data == 'export_tokens':
                await self.handlers['reports'].handle_export_tokens(update, context)
            
            # === Search & Bulk Operations ===
            elif callback_data == 'search_tokens':
                await self.handlers['dashboard'].handle_search_tokens(update, context)
            elif callback_data == 'bulk_delete_tokens':
                await self.handlers['cleanup'].handle_bulk_delete_tokens(update, context)
            elif callback_data.startswith('bulk_delete_'):
                await self.handlers['cleanup'].handle_bulk_delete_action(update, context)
            
            # === Users Management ===
            elif callback_data == 'list_users':
                await self.handlers['users'].handle_list_users(update, context)
            elif callback_data == 'search_user':
                await self.handlers['users'].handle_search_user(update, context)
            elif callback_data == 'import_users':
                await self.handlers['users'].show_import_users(update, context)
            elif callback_data == 'export_users':
                await self.handlers['users'].show_export_users(update, context)
            elif callback_data.startswith('user_details_'):
                await self.handlers['users'].show_user_details(update, context)
            elif callback_data.startswith('user_tokens_'):
                await self.handlers['users'].show_user_tokens(update, context)
            elif callback_data.startswith('deactivate_all_user_tokens_'):
                await self.handlers['users'].deactivate_all_user_tokens(update, context)
            
            # === Reports & Charts ===
            elif callback_data == 'usage_report':
                await self.handlers['reports'].show_usage_report(update, context)
            elif callback_data == 'anomaly_report':
                await self.handlers['reports'].show_anomaly_report(update, context)
            elif callback_data == 'quota_report':
                await self.handlers['reports'].show_quota_report(update, context)
            elif callback_data == 'compare_report':
                await self.handlers['reports'].show_compare_report(update, context)
            elif callback_data.startswith('export_format_'):
                await self.handlers['reports'].show_export_format_selection(update, context)
            
            # === Security & Expiry ===
            elif callback_data == 'expiry_settings':
                await self.handlers['security'].show_expiry_settings(update, context)
            elif callback_data == 'usage_limit_settings':
                await self.handlers['security'].show_usage_limit_settings(update, context)
            elif callback_data.startswith('set_def_expiry_'):
                await self.handlers['security_advanced'].show_set_default_expiry_menu(update, context) if callback_data == 'set_default_expiry' else await self.handlers['security'].handle_set_expiry_action(update, context)
            elif callback_data.startswith('set_usage_'):
                await self.handlers['security_advanced'].show_set_usage_limit_menu(update, context) if callback_data == 'set_usage_limit' else await self.handlers['security'].handle_set_expiry_action(update, context)
            
            # === Advanced Security Menu Items ===
            elif callback_data == 'manage_whitelist_ip':
                await self.handlers['security_advanced'].show_manage_whitelist_ip_menu(update, context)
            elif callback_data == 'manage_blacklist_ip':
                await self.handlers['security_advanced'].show_manage_blacklist_ip_menu(update, context)
            elif callback_data == 'add_ip_to_whitelist':
                await self.handlers['security_advanced'].show_add_ip_to_whitelist_menu(update, context)
            elif callback_data == 'remove_ip_from_whitelist':
                await self.handlers['security_advanced'].show_remove_ip_from_whitelist_menu(update, context)
            elif callback_data == 'import_whitelist_csv':
                await self.handlers['security_advanced'].show_import_whitelist_csv_menu(update, context)
            elif callback_data == 'alert_settings':
                await self.handlers['security_advanced'].show_alert_settings_menu(update, context)
            elif callback_data == 'threshold_failed_login':
                await self.handlers['security_advanced'].show_threshold_failed_login_menu(update, context)
            elif callback_data == '2fa_settings':
                await self.handlers['security_advanced'].show_2fa_settings_menu(update, context)
            elif callback_data == 'session_settings':
                await self.handlers['security_advanced'].show_session_settings_menu(update, context)
            elif callback_data == 'suspicious_analysis':
                await self.handlers['security_advanced'].show_suspicious_analysis_menu(update, context)
            
            # === Cleanup Operations Extended ===
            elif callback_data.startswith('confirm_cleanup_'):
                await self.handlers['cleanup'].handle_confirm_cleanup(update, context)
            elif callback_data.startswith('cleanup_unused_'):
                await self.handlers['cleanup'].preview_cleanup_unused(update, context)
            
            # === Unknown Callback ===
            else:
                logger.warning(f"Unknown token callback: {callback_data}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error in token callback routing: {e}")
            await update.callback_query.answer("❌ خطا در پردازش درخواست!")
            return False