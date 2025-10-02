#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Security Manager - مدیریت تنظیمات امنیتی و محدودیت‌های IP
"""

import aiosqlite
import json
import logging
import ipaddress
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from config.settings import settings

logger = logging.getLogger(__name__)


class SecurityManager:
    """مدیریت تنظیمات امنیتی سیستم"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        self.db_path = Path(self.db_path)
    
    async def init_security_tables(self):
        """Initialize security settings tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Security settings table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS security_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # IP Whitelist table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ip_whitelist (
                    id TEXT PRIMARY KEY,
                    ip_address TEXT NOT NULL,
                    ip_range TEXT,
                    description TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # IP Blacklist table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ip_blacklist (
                    id TEXT PRIMARY KEY,
                    ip_address TEXT NOT NULL,
                    ip_range TEXT,
                    reason TEXT,
                    blocked_by INTEGER,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Security alerts table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS security_alerts (
                    id TEXT PRIMARY KEY,
                    alert_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    message TEXT NOT NULL,
                    details TEXT DEFAULT '{}',
                    is_read BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            await db.execute('CREATE INDEX IF NOT EXISTS idx_security_settings_key ON security_settings(setting_key)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_ip_whitelist_ip ON ip_whitelist(ip_address)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_ip_blacklist_ip ON ip_blacklist(ip_address)')
            
            # Insert default settings if not exist
            await db.execute('''
                INSERT OR IGNORE INTO security_settings (setting_key, setting_value, description)
                VALUES 
                    ('default_expiry_days', '0', 'Default token expiry in days (0 = unlimited)'),
                    ('default_usage_limit', '0', 'Default usage limit (0 = unlimited)'),
                    ('ip_restrictions_enabled', 'false', 'Enable IP restrictions'),
                    ('security_alerts_enabled', 'true', 'Enable security alerts')
            ''')
            
            await db.commit()
    # === IP STATISTICS ===
    async def get_ip_statistics(self, limit: int = 10) -> Dict[str, Any]:
        """Return top IPs and suspicious IPs from download_sessions"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Top IPs by completed sessions in last 7 days
                cursor = await db.execute('''
                    SELECT ip_address, COUNT(*) as cnt
                    FROM download_sessions
                    WHERE started_at >= datetime('now', '-7 days') AND status = 'completed'
                    GROUP BY ip_address
                    ORDER BY cnt DESC
                    LIMIT ?
                ''', (limit,))
                top_rows = await cursor.fetchall()
                top_ips = [{'ip_address': r[0], 'count': r[1]} for r in top_rows]

                # Suspicious criterion: IPs with failures > 5 in last 24h or > 3 different link_code
                cursor = await db.execute('''
                    SELECT ip_address,
                           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures,
                           COUNT(DISTINCT link_code) as distinct_links,
                           COUNT(*) as total
                    FROM download_sessions
                    WHERE started_at >= datetime('now', '-1 day')
                    GROUP BY ip_address
                    HAVING failures >= 5 OR distinct_links >= 3
                    ORDER BY failures DESC, distinct_links DESC
                    LIMIT ?
                ''', (limit,))
                susp_rows = await cursor.fetchall()
                suspicious_ips = [
                    {
                        'ip_address': r[0],
                        'failures': r[1],
                        'distinct_links': r[2],
                        'total': r[3]
                    } for r in susp_rows
                ]

                return {
                    'top_ips': top_ips,
                    'suspicious_ips': suspicious_ips,
                    'generated_at': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting IP statistics: {e}")
            return {'top_ips': [], 'suspicious_ips': [], 'error': str(e)}

            logger.info("Security tables initialized successfully")
    
    # === SECURITY SETTINGS ===
    
    async def get_setting(self, key: str) -> Optional[str]:
        """Get a security setting value"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT setting_value FROM security_settings WHERE setting_key = ?
            ''', (key,))
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def set_setting(self, key: str, value: str, description: str = None) -> bool:
        """Set a security setting"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO security_settings (setting_key, setting_value, description, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(setting_key) DO UPDATE SET
                        setting_value = excluded.setting_value,
                        description = COALESCE(excluded.description, description),
                        updated_at = CURRENT_TIMESTAMP
                ''', (key, value, description))
                await db.commit()
                logger.info(f"Security setting updated: {key} = {value}")
                return True
            except Exception as e:
                logger.error(f"Error setting security setting: {e}")
                return False
    
    async def get_all_settings(self) -> Dict[str, Any]:
        """Get all security settings"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM security_settings')
            rows = await cursor.fetchall()
            return {row['setting_key']: row['setting_value'] for row in rows}
    
    # === DEFAULT EXPIRY ===
    
    async def set_default_expiry(self, days: int) -> bool:
        """Set default token expiry in days (0 = unlimited)"""
        return await self.set_setting(
            'default_expiry_days',
            str(days),
            f'Default token expiry: {days} days' if days > 0 else 'Unlimited expiry'
        )
    
    async def get_default_expiry(self) -> int:
        """Get default expiry days"""
        value = await self.get_setting('default_expiry_days')
        return int(value) if value else 0
    
    # === USAGE LIMIT ===
    
    async def set_usage_limit(self, limit: int) -> bool:
        """Set default usage limit (0 = unlimited)"""
        return await self.set_setting(
            'default_usage_limit',
            str(limit),
            f'Default usage limit: {limit}' if limit > 0 else 'Unlimited usage'
        )
    
    async def get_usage_limit(self) -> int:
        """Get default usage limit"""
        value = await self.get_setting('default_usage_limit')
        return int(value) if value else 0
    
    # === IP RESTRICTIONS ===
    
    async def enable_ip_restrictions(self) -> bool:
        """Enable IP restrictions"""
        return await self.set_setting('ip_restrictions_enabled', 'true', 'IP restrictions enabled')
    
    async def disable_ip_restrictions(self) -> bool:
        """Disable IP restrictions"""
        return await self.set_setting('ip_restrictions_enabled', 'false', 'IP restrictions disabled')
    
    async def are_ip_restrictions_enabled(self) -> bool:
        """Check if IP restrictions are enabled"""
        value = await self.get_setting('ip_restrictions_enabled')
        return value == 'true' if value else False
    
    # === IP WHITELIST ===
    
    async def add_to_whitelist(
        self, 
        ip_address: str, 
        description: str = None, 
        created_by: int = None
    ) -> Optional[str]:
        """Add IP or IP range to whitelist"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Validate IP address or range
                ip_range = None
                try:
                    if '/' in ip_address:
                        # CIDR notation
                        ipaddress.ip_network(ip_address, strict=False)
                        ip_range = ip_address
                    else:
                        # Single IP
                        ipaddress.ip_address(ip_address)
                except ValueError:
                    logger.error(f"Invalid IP address: {ip_address}")
                    return None
                
                whitelist_id = str(uuid.uuid4())
                await db.execute('''
                    INSERT INTO ip_whitelist (id, ip_address, ip_range, description, created_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', (whitelist_id, ip_address, ip_range, description, created_by))
                await db.commit()
                logger.info(f"IP added to whitelist: {ip_address}")
                return whitelist_id
            except Exception as e:
                logger.error(f"Error adding IP to whitelist: {e}")
                return None
    
    async def remove_from_whitelist(self, whitelist_id: str) -> bool:
        """Remove IP from whitelist"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    UPDATE ip_whitelist SET is_active = 0 WHERE id = ?
                ''', (whitelist_id,))
                await db.commit()
                logger.info(f"IP removed from whitelist: {whitelist_id}")
                return True
            except Exception as e:
                logger.error(f"Error removing IP from whitelist: {e}")
                return False
    
    async def get_whitelist(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all whitelisted IPs"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = 'SELECT * FROM ip_whitelist'
            if active_only:
                query += ' WHERE is_active = 1'
            query += ' ORDER BY created_at DESC'
            
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def is_ip_whitelisted(self, ip_address: str) -> bool:
        """Check if IP is in whitelist"""
        whitelist = await self.get_whitelist(active_only=True)
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            for entry in whitelist:
                if entry['ip_range']:
                    # Check if IP is in range
                    network = ipaddress.ip_network(entry['ip_range'], strict=False)
                    if ip in network:
                        return True
                elif entry['ip_address'] == ip_address:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking IP whitelist: {e}")
            return False
    
    # === IP BLACKLIST ===
    
    async def add_to_blacklist(
        self, 
        ip_address: str, 
        reason: str = None, 
        blocked_by: int = None
    ) -> Optional[str]:
        """Add IP to blacklist"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Validate IP
                ip_range = None
                try:
                    if '/' in ip_address:
                        ipaddress.ip_network(ip_address, strict=False)
                        ip_range = ip_address
                    else:
                        ipaddress.ip_address(ip_address)
                except ValueError:
                    logger.error(f"Invalid IP address: {ip_address}")
                    return None
                
                blacklist_id = str(uuid.uuid4())
                await db.execute('''
                    INSERT INTO ip_blacklist (id, ip_address, ip_range, reason, blocked_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', (blacklist_id, ip_address, ip_range, reason, blocked_by))
                await db.commit()
                logger.info(f"IP added to blacklist: {ip_address}")
                return blacklist_id
            except Exception as e:
                logger.error(f"Error adding IP to blacklist: {e}")
                return None
    
    async def remove_from_blacklist(self, blacklist_id: str) -> bool:
        """Remove IP from blacklist"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    UPDATE ip_blacklist SET is_active = 0 WHERE id = ?
                ''', (blacklist_id,))
                await db.commit()
                logger.info(f"IP removed from blacklist: {blacklist_id}")
                return True
            except Exception as e:
                logger.error(f"Error removing IP from blacklist: {e}")
                return False
    
    async def get_blacklist(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all blacklisted IPs"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = 'SELECT * FROM ip_blacklist'
            if active_only:
                query += ' WHERE is_active = 1'
            query += ' ORDER BY blocked_at DESC'
            
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def is_ip_blacklisted(self, ip_address: str) -> bool:
        """Check if IP is in blacklist"""
        blacklist = await self.get_blacklist(active_only=True)
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            for entry in blacklist:
                if entry['ip_range']:
                    network = ipaddress.ip_network(entry['ip_range'], strict=False)
                    if ip in network:
                        return True
                elif entry['ip_address'] == ip_address:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking IP blacklist: {e}")
            return False
    
    # === IP VALIDATION ===
    
    async def validate_ip_access(self, ip_address: str) -> Dict[str, Any]:
        """Validate if IP has access (check restrictions, whitelist, blacklist)"""
        result = {
            'allowed': True,
            'reason': None
        }
        
        # Check blacklist first
        if await self.is_ip_blacklisted(ip_address):
            result['allowed'] = False
            result['reason'] = 'IP is blacklisted'
            return result
        
        # Check whitelist if restrictions are enabled
        if await self.are_ip_restrictions_enabled():
            if not await self.is_ip_whitelisted(ip_address):
                result['allowed'] = False
                result['reason'] = 'IP not in whitelist'
                return result
        
        return result
    
    # === SECURITY ALERTS ===
    
    async def create_alert(
        self, 
        alert_type: str, 
        message: str, 
        severity: str = 'medium',
        details: Dict[str, Any] = None
    ) -> str:
        """Create a security alert"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                alert_id = str(uuid.uuid4())
                details_json = json.dumps(details or {})
                
                await db.execute('''
                    INSERT INTO security_alerts (id, alert_type, severity, message, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (alert_id, alert_type, severity, message, details_json))
                await db.commit()
                logger.info(f"Security alert created: {alert_type}")
                return alert_id
            except Exception as e:
                logger.error(f"Error creating security alert: {e}")
                return None
    
    async def get_alerts(
        self, 
        unread_only: bool = False, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get security alerts"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = 'SELECT * FROM security_alerts'
            if unread_only:
                query += ' WHERE is_read = 0'
            query += ' ORDER BY created_at DESC LIMIT ?'
            
            cursor = await db.execute(query, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def mark_alert_as_read(self, alert_id: str) -> bool:
        """Mark alert as read"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    UPDATE security_alerts SET is_read = 1 WHERE id = ?
                ''', (alert_id,))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error marking alert as read: {e}")
                return False
    
    async def clear_old_alerts(self, days: int = 30) -> int:
        """Clear alerts older than specified days"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                cursor = await db.execute('''
                    DELETE FROM security_alerts WHERE created_at < ?
                ''', (cutoff_date,))
                await db.commit()
                return cursor.rowcount
            except Exception as e:
                logger.error(f"Error clearing old alerts: {e}")
                return 0