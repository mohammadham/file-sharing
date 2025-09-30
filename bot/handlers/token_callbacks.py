#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Management Callbacks Router - مسیریابی callback های مدیریت توکن
"""

import logging
from datetime import datetime, timedelta
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
                if 'search' in self.handlers:
                    await self.handlers['search'].show_advanced_search_menu(update, context)
                else:
                    await self.handlers['dashboard'].show_advanced_search_menu(update, context)
            elif callback_data == 'bulk_delete_tokens':
                await self.handlers['cleanup'].handle_bulk_delete_tokens(update, context)
            elif callback_data.startswith('bulk_delete_'):
                await self.handlers['cleanup'].handle_bulk_delete_action(update, context)
            elif callback_data == 'bulk_actions':
                await self.handlers['dashboard'].show_bulk_actions_menu(update, context)
            elif callback_data == 'edit_tokens_menu':
                await self.handlers['dashboard'].show_edit_tokens_menu(update, context)
            elif callback_data == 'delete_tokens_menu':
                await self.handlers['dashboard'].show_delete_tokens_menu(update, context)
            
            # === Advanced Search Operations ===
            elif callback_data.startswith('search_by_'):
                if 'search' in self.handlers:
                    if callback_data == 'search_by_name':
                        await self.handlers['search'].search_by_name(update, context)
                    elif callback_data == 'search_by_type':
                        await self.handlers['search'].search_by_type(update, context)
                    elif callback_data == 'search_by_status':
                        await self.handlers['search'].search_by_status(update, context)
                    elif callback_data in ['search_by_date_range', 'search_by_date']:  # Support both for compatibility
                        await self.handlers['search'].search_by_date_range(update, context)
                    elif callback_data == 'search_by_ip':
                        await self.handlers['search'].search_by_ip(update, context)
                    elif callback_data == 'search_by_usage':
                        await self.handlers['search'].search_by_usage(update, context)  # Fixed: was going to dashboard
                    elif callback_data == 'search_by_country':
                        await self.handlers['search'].handle_search_by_country(update, context)
                    else:
                        await self.handlers['dashboard'].handle_advanced_search_action(update, context)
                else:
                    await self.handlers['dashboard'].handle_advanced_search_action(update, context)
            elif callback_data == 'combined_search':
                if 'search' in self.handlers:
                    await self.handlers['search'].show_combined_search(update, context)  # Fixed: was going to dashboard
                else:
                    await self.handlers['dashboard'].show_combined_search(update, context)
            elif callback_data == 'save_search':
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_save_search(update, context)  # Fixed: was going to dashboard
                else:
                    await self.handlers['dashboard'].handle_save_search(update, context)
            elif callback_data == 'recent_searches':
                if 'search' in self.handlers:
                    await self.handlers['search'].show_recent_searches(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'clear_search_history':
                if 'search' in self.handlers:
                    await self.handlers['search'].clear_search_history(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            
            # === Saved Searches Operations ===
            elif callback_data == 'show_saved_searches':
                if 'search' in self.handlers:
                    await self.handlers['search'].show_saved_searches(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('load_saved_search_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_load_saved_search(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('delete_saved_search_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_delete_saved_search(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('save_search_name_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_confirm_save_search(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            
            # === Export & Stats Operations ===
            elif callback_data.startswith('export_search_results_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_export_search_results(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('export_format_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_export_format(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('search_results_stats_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_search_results_stats(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            
            # === Combined Search Filter Operations ===
            elif callback_data in ['add_type_filter', 'add_status_filter', 'add_date_filter', 'add_usage_filter']:
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_add_filter(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'execute_combined_search':
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_execute_combined_search(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'clear_combined_filters':
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_clear_combined_filters(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            
            # === Filter Operations ===
            elif callback_data.startswith('filter_type_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_filter_type(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('filter_status_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_filter_status(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('filter_date_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_filter_date(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('filter_usage_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_filter_usage(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('filter_country_'):
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_filter_country(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            
            # === IP Search Operations ===
            elif callback_data == 'search_specific_ip':
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_search_specific_ip(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'search_ip_range':
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_search_ip_range(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'search_suspicious_ips':
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_search_suspicious_ips(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'search_top_ips':
                if 'search' in self.handlers:
                    await self.handlers['search'].handle_search_top_ips(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'common_ip_ranges':
                if 'search' in self.handlers:
                    await update.callback_query.answer("🚧 محدوده‌های رایج IP - در حال توسعه")
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'all_countries_list':
                if 'search' in self.handlers:
                    await update.callback_query.answer("🚧 لیست کامل کشورها - در حال توسعه")
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('search_results_'):
                if 'search' in self.handlers:
                    # Use the new pagination handler
                    await self.handlers['search'].handle_paginated_results(update, context)
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data.startswith('repeat_search_'):
                if 'search' in self.handlers:
                    # Extract search index
                    search_idx = int(callback_data.split('_')[-1])
                    recent_searches = context.user_data.get('recent_searches', [])
                    if 0 <= search_idx < len(recent_searches):
                        search = recent_searches[search_idx]
                        search_type = search['type']
                        search_value = search['value']
                        
                        # Re-execute the search based on type
                        result = None
                        if search_type == 'type':
                            result = await self.handlers['management'].search_tokens_by_type(search_value)
                        elif search_type == 'status':
                            result = await self.handlers['management'].search_tokens_by_status(search_value)
                        elif search_type == 'name':
                            result = await self.handlers['management'].search_tokens_by_name(search_value)
                        elif search_type in ['ip', 'specific_ip']:
                            result = await self.handlers['management'].search_tokens_by_ip(search_value)
                        elif search_type == 'ip_range':
                            result = await self.handlers['management'].search_tokens_by_ip_range(search_value)
                        elif search_type == 'usage':
                            # Parse usage range
                            usage_parts = search_value.split('_')
                            min_usage = int(usage_parts[0]) if len(usage_parts) > 0 else 0
                            max_usage = int(usage_parts[1]) if len(usage_parts) > 1 and usage_parts[1] != 'unlimited' else None
                            result = await self.handlers['management'].search_tokens_by_usage(min_usage, max_usage)
                        elif search_type == 'date':
                            # Parse date range
                            end_date = datetime.now()
                            if search_value == 'today':
                                start_date = end_date.replace(hour=0, minute=0, second=0)
                            elif search_value == 'week':
                                start_date = end_date - timedelta(days=7)
                            elif search_value == 'month':
                                start_date = end_date - timedelta(days=30)
                            elif search_value == '3months':
                                start_date = end_date - timedelta(days=90)
                            else:
                                start_date = datetime(2020, 1, 1)
                            result = await self.handlers['management'].search_tokens_by_date_range(start_date, end_date)
                        elif search_type == 'country':
                            result = await self.handlers['management'].search_tokens_by_country(search_value)
                        elif search_type == 'combined':
                            # Re-execute combined search
                            result = await self.handlers['management'].get_all_tokens()
                        else:
                            result = {'success': True, 'tokens': []}
                        
                        await self.handlers['search']._display_search_results(
                            update, context, result, f"🔄 تکرار: {search['display_name']}", search_type, search_value
                        )
                    else:
                        await update.callback_query.answer("❌ جستجو یافت نشد")
                else:
                    await update.callback_query.answer("🚧 در حال توسعه")
            
            # === Bulk Operations Detailed ===
            elif callback_data.startswith('bulk_'):
                await self.handlers['dashboard'].handle_bulk_operation(update, context)
            elif callback_data.startswith('edit_token_'):
                await self.handlers['dashboard'].handle_token_edit_action(update, context)
            elif callback_data.startswith('delete_'):
                await self.handlers['dashboard'].handle_token_delete_action(update, context)
            
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
            
            # === System Management Menu ===
            elif callback_data == 'system_menu':
                await self.handlers['system'].show_system_menu(update, context)
            elif callback_data == 'backup_menu':
                await self.handlers['system'].show_backup_menu(update, context)
            elif callback_data == 'create_backup_now':
                await self.handlers['system'].create_backup_now(update, context)
            elif callback_data == 'download_backup':
                await self.handlers['system'].handle_download_backup(update, context)
            elif callback_data == 'restore_backup':
                await self.handlers['system'].handle_restore_backup(update, context)
            elif callback_data == 'schedule_backup':
                await self.handlers['system'].handle_schedule_backup(update, context)
            elif callback_data == 'health_menu':
                await self.handlers['system'].show_health_menu(update, context)
            elif callback_data == 'detailed_health':
                await self.handlers['system'].show_health_menu(update, context)  # Refresh health
            elif callback_data == 'logs_menu':
                await self.handlers['system'].show_logs_menu(update, context)
            elif callback_data == 'view_system_log':
                await self.handlers['system'].handle_view_system_log(update, context)
            elif callback_data == 'download_log':
                await self.handlers['system'].handle_download_log(update, context)
            elif callback_data == 'clear_old_logs':
                await self.handlers['system'].handle_clear_old_logs(update, context)
            elif callback_data == 'log_settings':
                await self.handlers['system'].handle_log_settings(update, context)
            elif callback_data == 'language_menu':
                await self.handlers['system'].show_language_menu(update, context)
            elif callback_data.startswith('set_'):
                if callback_data in ['set_persian', 'set_english', 'set_auto']:
                    await self.handlers['system'].handle_set_language(update, context)
            elif callback_data == 'reset_system_menu':
                await self.handlers['system'].show_reset_system_menu(update, context)
            elif callback_data == 'type_password_reset':
                await self.handlers['system'].handle_type_password_reset(update, context)
            
            # === Advanced Analytics Menu ===
            elif callback_data == 'advanced_analytics':
                await self.handlers['analytics'].show_advanced_analytics_menu(update, context)
            elif callback_data == 'usage_charts':
                await self.handlers['analytics'].show_usage_charts(update, context)
            elif callback_data == 'behavior_analysis':
                await self.handlers['analytics'].show_behavior_analysis(update, context)
            elif callback_data == 'trend_prediction':
                await self.handlers['analytics'].show_trend_prediction(update, context)
            elif callback_data == 'performance_stats':
                await self.handlers['analytics'].show_performance_stats(update, context)
            elif callback_data == 'geo_analysis':
                await self.handlers['analytics'].show_geo_analysis(update, context)
            elif callback_data == 'optimization_recommendations':
                await self.handlers['analytics'].show_optimization_recommendations(update, context)
            
            # === Token Edit Operations ===
            elif callback_data.startswith('edit_token_'):
                await self.handlers['dashboard'].handle_edit_token(update, context)
            elif callback_data.startswith('edit_name_'):
                await self.handlers['dashboard'].handle_edit_token_name(update, context)
            elif callback_data.startswith('edit_expiry_'):
                await self.handlers['dashboard'].handle_edit_token_expiry(update, context)
            elif callback_data.startswith('edit_type_'):
                await self.handlers['dashboard'].handle_edit_token_type(update, context)
            elif callback_data.startswith('edit_quota_'):
                await self.handlers['dashboard'].handle_edit_token_quota(update, context)
            elif callback_data.startswith('save_changes_'):
                await self.handlers['dashboard'].handle_save_token_changes(update, context)
            
            # === Token Actions - Set Operations ===
            elif callback_data.startswith('set_name_'):
                await self.handlers['dashboard'].handle_set_token_name(update, context)
            elif callback_data.startswith('set_expiry_'):
                await self.handlers['dashboard'].handle_set_token_expiry(update, context)
            elif callback_data.startswith('set_type_'):
                await self.handlers['dashboard'].handle_set_token_type(update, context)
            elif callback_data.startswith('set_quota_'):
                await self.handlers['dashboard'].handle_set_token_quota(update, context)
            
            # === Token Deactivation ===
            elif callback_data.startswith('deactivate_token_'):
                await self.handlers['dashboard'].handle_deactivate_token(update, context)
            elif callback_data.startswith('confirm_deactivate_'):
                await self.handlers['dashboard'].handle_confirm_deactivate_token(update, context)
            
            # === Token Statistics ===
            elif callback_data.startswith('token_stats_'):
                await self.handlers['dashboard'].handle_token_stats(update, context)
            elif callback_data.startswith('token_access_log_'):
                await self.handlers['dashboard'].handle_token_access_log(update, context)
            elif callback_data.startswith('token_anomaly_'):
                await self.handlers['dashboard'].handle_token_anomaly(update, context)
            elif callback_data.startswith('export_token_report_'):
                await self.handlers['dashboard'].handle_export_token_report(update, context)
            
            # === Token Type Comparison ===
            elif callback_data.startswith('compare_types_'):
                await self.handlers['dashboard'].handle_compare_token_types(update, context)
            
            # === Custom Token Operations ===
            elif callback_data.startswith('custom_name_'):
                await self.handlers['dashboard'].handle_custom_token_name(update, context)
            elif callback_data.startswith('custom_expiry_'):
                await self.handlers['dashboard'].handle_custom_token_expiry(update, context)
            elif callback_data.startswith('custom_quota_'):
                await self.handlers['dashboard'].handle_custom_token_quota(update, context)
            
            # === Token Reactivation ===
            elif callback_data.startswith('reactivate_token_'):
                await self.handlers['dashboard'].handle_reactivate_token(update, context)
            
            # === Advanced Search Operations Extended ===
            elif callback_data.startswith('search_by_'):
                await self.handlers['dashboard'].handle_advanced_search_action(update, context) if hasattr(self.handlers['dashboard'], 'handle_advanced_search_action') else await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'combined_search':
                await self.handlers['dashboard'].show_combined_search(update, context) if hasattr(self.handlers['dashboard'], 'show_combined_search') else await update.callback_query.answer("🚧 در حال توسعه")
            elif callback_data == 'save_search':
                await self.handlers['dashboard'].handle_save_search(update, context) if hasattr(self.handlers['dashboard'], 'handle_save_search') else await update.callback_query.answer("🚧 در حال توسعه")
            
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