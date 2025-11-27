"""
Surveillance Field Metadata for UI Integration.

This module provides comprehensive metadata for all surveillance database fields,
including labels, descriptions, value definitions, and severity levels.

Based on specification: .claude/file-formats-surveillance.md
NSE Circular: NSE/SURV/65097 dated November 14, 2024
"""
from typing import Dict, Any


class SurveillanceFieldMetadata:
    """
    Metadata for surveillance database fields - descriptions and labels for UI integration.

    Usage:
        # Get field metadata for API response
        field_info = SurveillanceFieldMetadata.SURVEILLANCE_LIST_FIELDS['gsm_stage']

        # Build dropdown options for UI
        options = field_info['values']

        # Display field description in tooltip
        description = field_info['description']
    """

    # ========== SURVEILLANCE_LIST FIELDS (Core Measures + Binary Flags) ==========

    SURVEILLANCE_LIST_FIELDS: Dict[str, Dict[str, Any]] = {
        # Metadata Fields
        'symbol': {
            'label': 'Symbol',
            'description': 'NSE security symbol (e.g., RELIANCE, TCS)',
            'type': 'string',
            'category': 'metadata'
        },
        'date': {
            'label': 'Date',
            'description': 'Data ingestion date for daily historical tracking',
            'type': 'date',
            'category': 'metadata'
        },
        'nse_exclusive': {
            'label': 'NSE Exclusive',
            'description': 'Whether security is exclusively listed on NSE',
            'type': 'string',
            'values': {'Y': 'NSE Exclusive', 'N': 'Also listed elsewhere'},
            'category': 'metadata'
        },
        'status': {
            'label': 'Status',
            'description': 'Current trading status of the security',
            'type': 'string',
            'values': {'A': 'Active', 'S': 'Suspended', 'I': 'Inactive'},
            'category': 'metadata'
        },
        'series': {
            'label': 'Series',
            'description': 'Trading series classification',
            'type': 'string',
            'values': {
                'EQ': 'Equity',
                'BE': 'Book Entry',
                'BZ': 'BZ Series (compliance issues)',
                'SM': 'SME',
                'ST': 'ST Series'
            },
            'category': 'metadata'
        },

        # Staged Surveillance Measures
        'gsm_stage': {
            'label': 'GSM Stage',
            'description': 'Graded Surveillance Measure - Progressive surveillance stages (0-6) for unusual price/volume patterns',
            'type': 'smallint',
            'values': {
                0: 'Stage 0 - Identified',
                1: 'Stage 1 - Price band 5%, trade for trade',
                2: 'Stage 2 - Price band 5%, periodic call auction',
                3: 'Stage 3 - Price band 2.5%, periodic call auction',
                4: 'Stage 4 - ASM framework, 100% margin',
                5: 'Stage 5 - Additional restrictions',
                6: 'Stage 6 - Maximum surveillance'
            },
            'severity': 'high',
            'category': 'staged_measure',
            'tooltip': 'Higher stages indicate increasing regulatory scrutiny due to unusual trading activity'
        },
        'long_term_asm_stage': {
            'label': 'Long Term ASM',
            'description': 'Long Term Additional Surveillance Measure (1-4) for sustained unusual activity',
            'type': 'smallint',
            'values': {
                1: 'Stage 1 - Initial surveillance',
                2: 'Stage 2 - Enhanced monitoring',
                3: 'Stage 3 - Strict surveillance',
                4: 'Stage 4 - Maximum restrictions'
            },
            'severity': 'high',
            'category': 'staged_measure',
            'tooltip': 'Applied when unusual activity persists over extended periods'
        },
        'short_term_asm_stage': {
            'label': 'Short Term ASM',
            'description': 'Short Term Additional Surveillance Measure (1-2) for recent unusual activity',
            'type': 'smallint',
            'values': {
                1: 'Stage 1 - Recent activity flagged',
                2: 'Stage 2 - Heightened short-term surveillance'
            },
            'severity': 'medium',
            'category': 'staged_measure',
            'tooltip': 'Indicates recent unusual trading patterns that may be temporary'
        },
        'sms_category': {
            'label': 'SMS Category',
            'description': 'Unsolicited SMS surveillance category for securities mentioned in SMS campaigns',
            'type': 'smallint',
            'values': {
                0: 'Informational - Mentioned in SMS',
                1: 'Watchlist - Active SMS campaign detected'
            },
            'severity': 'medium',
            'category': 'staged_measure',
            'tooltip': 'Securities being promoted through unsolicited SMS messages'
        },
        'irp_stage': {
            'label': 'IRP Stage',
            'description': 'Insolvency Resolution Process stage (0-2) under IBC proceedings',
            'type': 'smallint',
            'values': {
                0: 'Stage 0 - IRP initiated',
                1: 'Stage 1 - Under resolution',
                2: 'Stage 2 - Advanced insolvency proceedings'
            },
            'severity': 'critical',
            'category': 'staged_measure',
            'tooltip': 'Company is undergoing insolvency proceedings under Insolvency and Bankruptcy Code'
        },
        'default_stage': {
            'label': 'Default Stage',
            'description': 'Payment default stage (0-1) for company disclosed payment defaults',
            'type': 'smallint',
            'values': {
                0: 'Stage 0 - Default identified',
                1: 'Stage 1 - Persistent default'
            },
            'severity': 'critical',
            'category': 'staged_measure',
            'tooltip': 'Company has disclosed payment defaults to lenders or debt holders'
        },
        'ica_stage': {
            'label': 'ICA Stage',
            'description': 'Interconnected Agreements stage (0-1) for related party transactions under surveillance',
            'type': 'smallint',
            'values': {
                0: 'Stage 0 - ICA identified',
                1: 'Stage 1 - Under scrutiny'
            },
            'severity': 'high',
            'category': 'staged_measure',
            'tooltip': 'Related party transactions or interconnected agreements under regulatory surveillance'
        },
        'esm_stage': {
            'label': 'ESM Stage',
            'description': 'Enhanced Surveillance Measure stage (1-2) - Most common surveillance indicator',
            'type': 'smallint',
            'values': {
                1: 'Stage 1 - Enhanced surveillance',
                2: 'Stage 2 - Stricter surveillance'
            },
            'severity': 'high',
            'category': 'staged_measure',
            'tooltip': 'Most frequently applied surveillance measure for securities with unusual activity'
        },

        # Binary Surveillance Flags
        'high_promoter_pledge': {
            'label': 'High Promoter Pledge',
            'description': 'Promoter shareholding pledged above NSE threshold',
            'type': 'boolean',
            'severity': 'high',
            'category': 'binary_flag',
            'tooltip': 'High promoter pledge can indicate financial stress or risk of shareholding transfer'
        },
        'addon_price_band': {
            'label': 'Add-on Price Band',
            'description': 'Additional price band restrictions applied beyond normal limits',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'binary_flag',
            'tooltip': 'Stricter daily price movement limits imposed to curb volatility'
        },
        'total_pledge_measure': {
            'label': 'Total Pledge Measure',
            'description': 'Promoter + Non-Promoter pledge holdings exceed NSE threshold',
            'type': 'boolean',
            'severity': 'high',
            'category': 'binary_flag',
            'tooltip': 'Combined pledge levels indicate significant encumbrance of shareholding'
        },
        'social_media_platforms': {
            'label': 'Social Media Flag',
            'description': 'Flagged due to social media mentions, campaigns, or unusual online activity',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'binary_flag',
            'tooltip': 'Security is being actively discussed or promoted on social media platforms'
        }
    }

    # ========== SURVEILLANCE_FUNDAMENTAL_FLAGS (Financial/Compliance Risks) ==========

    FUNDAMENTAL_FLAGS_FIELDS: Dict[str, Dict[str, Any]] = {
        # Financial Risk Flags
        'is_loss_making': {
            'label': 'Loss Making',
            'description': '≥8 quarters loss (mainboard) or ≥2 years (SME) on consolidated basis',
            'type': 'boolean',
            'severity': 'critical',
            'category': 'financial_risk',
            'tooltip': 'Company has sustained losses indicating financial distress'
        },
        'encumbrance_over_50pct': {
            'label': 'High Encumbrance (>50%)',
            'description': 'Promoter/promoter group encumbrance ≥50% of total capital',
            'type': 'boolean',
            'severity': 'critical',
            'category': 'financial_risk',
            'tooltip': 'Majority of promoter holdings are pledged, indicating high financial leverage'
        },
        'eps_zero_or_negative': {
            'label': 'Zero/Negative EPS',
            'description': 'EPS zero or negative for 4 trailing quarters (aggregated)',
            'type': 'boolean',
            'severity': 'high',
            'category': 'financial_risk',
            'tooltip': 'Company has not generated positive earnings per share'
        },

        # Compliance Flags
        'under_bz_sz_series': {
            'label': 'BZ/SZ Series',
            'description': 'In BZ/SZ series due to SEBI SOP Circular non-compliance',
            'type': 'boolean',
            'severity': 'critical',
            'category': 'compliance',
            'tooltip': 'Company has not complied with SEBI regulations and is in restricted trading series'
        },
        'listing_fee_unpaid': {
            'label': 'Listing Fee Unpaid',
            'description': 'Failed to pay annual listing fee to exchange',
            'type': 'boolean',
            'severity': 'high',
            'category': 'compliance',
            'tooltip': 'Company has not paid required exchange listing fees'
        },

        # Liquidity/Market Flags
        'fo_exit_scheduled': {
            'label': 'F&O Exit Scheduled',
            'description': 'Derivative contracts exiting F&O segment (no new far-month contracts)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'liquidity',
            'tooltip': 'Futures & Options contracts will not be renewed, indicating declining derivative interest'
        },
        'low_unique_pan_traded': {
            'label': 'Low Participation (<100 PANs)',
            'description': '<100 unique PAN cards traded in previous 30 days (low participation)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'liquidity',
            'tooltip': 'Very low investor participation may indicate illiquidity'
        },
        'sme_mm_period_over': {
            'label': 'SME Market Making Ended',
            'description': 'SME mandatory market-making period ended (exit may be difficult)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'liquidity',
            'tooltip': 'Market makers no longer required to provide liquidity for this SME stock'
        },
        'sme_not_regularly_traded': {
            'label': 'SME Not Regularly Traded',
            'description': 'SME security not regularly traded (exit may be difficult)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'liquidity',
            'tooltip': 'Infrequent trading makes it difficult to buy or sell shares'
        },

        # Valuation Flag
        'pe_over_50': {
            'label': 'P/E Ratio >50',
            'description': 'P/E ratio >50 based on 4 trailing quarters',
            'type': 'boolean',
            'severity': 'low',
            'category': 'valuation',
            'tooltip': 'High P/E ratio may indicate overvaluation or growth expectations'
        }
    }

    # ========== SURVEILLANCE_PRICE_MOVEMENT (Close-to-Close Movements) ==========

    PRICE_MOVEMENT_FIELDS: Dict[str, Dict[str, Any]] = {
        'c2c_25pct_5d': {
            'label': '>25% in 5 Days',
            'description': 'Close-to-close price movement >25% in 5 trading days',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'short_term_momentum',
            'period': '5 days',
            'threshold': '25%',
            'tooltip': 'Rapid short-term price appreciation'
        },
        'c2c_40pct_15d': {
            'label': '>40% in 15 Days',
            'description': 'Close-to-close price movement >40% in 15 trading days',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'short_term_momentum',
            'period': '15 days',
            'threshold': '40%',
            'tooltip': 'Strong short-term price movement'
        },
        'c2c_100pct_60d': {
            'label': '>100% in 60 Days (Doubled)',
            'description': 'Close-to-close price movement >100% in 60 trading days (stock price doubled)',
            'type': 'boolean',
            'severity': 'high',
            'category': 'medium_term_momentum',
            'period': '60 days',
            'threshold': '100%',
            'tooltip': 'Stock price has doubled in 2 months - high momentum indicator'
        },
        'c2c_25pct_15d': {
            'label': '>25% in 15 Days (Alt)',
            'description': 'Close-to-close price movement >25% in 15 days (alternate threshold)',
            'type': 'boolean',
            'severity': 'low',
            'category': 'short_term_momentum',
            'period': '15 days',
            'threshold': '25%',
            'tooltip': 'Moderate short-term price movement'
        },
        'c2c_50pct_1m': {
            'label': '>50% in 1 Month',
            'description': 'Close-to-close price movement >50% in 1 month',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'short_term_momentum',
            'period': '1 month',
            'threshold': '50%',
            'tooltip': 'Significant monthly price appreciation'
        },
        'c2c_90pct_3m': {
            'label': '>90% in 3 Months',
            'description': 'Close-to-close price movement >90% in 3 months',
            'type': 'boolean',
            'severity': 'high',
            'category': 'medium_term_momentum',
            'period': '3 months',
            'threshold': '90%',
            'tooltip': 'Near doubling of price in quarterly timeframe'
        },
        'c2c_25pct_1m_alt': {
            'label': '>25% in 1 Month (Alt)',
            'description': 'Close-to-close price movement >25% in 1 month (alternate threshold)',
            'type': 'boolean',
            'severity': 'low',
            'category': 'short_term_momentum',
            'period': '1 month',
            'threshold': '25%',
            'tooltip': 'Moderate monthly price movement'
        },
        'c2c_50pct_3m': {
            'label': '>50% in 3 Months',
            'description': 'Close-to-close price movement >50% in 3 months',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'medium_term_momentum',
            'period': '3 months',
            'threshold': '50%',
            'tooltip': 'Strong quarterly price appreciation'
        },
        'c2c_200pct_365d': {
            'label': '>200% in 365 Days (Tripled)',
            'description': 'Close-to-close price movement >200% in 365 days (stock price tripled)',
            'type': 'boolean',
            'severity': 'high',
            'category': 'long_term_momentum',
            'period': '365 days',
            'threshold': '200%',
            'tooltip': 'Stock price has tripled in 1 year - exceptional annual performance'
        },
        'c2c_75pct_6m': {
            'label': '>75% in 6 Months',
            'description': 'Close-to-close price movement >75% in 6 months',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'medium_term_momentum',
            'period': '6 months',
            'threshold': '75%',
            'tooltip': 'Strong half-yearly price appreciation'
        },
        'c2c_100pct_365d': {
            'label': '>100% in 365 Days (Doubled)',
            'description': 'Close-to-close price movement >100% in 365 days (stock price doubled)',
            'type': 'boolean',
            'severity': 'high',
            'category': 'long_term_momentum',
            'period': '365 days',
            'threshold': '100%',
            'tooltip': 'Stock price has doubled in 1 year - strong annual performance'
        }
    }

    # ========== SURVEILLANCE_PRICE_VARIATION (High-Low Volatility) ==========

    PRICE_VARIATION_FIELDS: Dict[str, Dict[str, Any]] = {
        'hl_75pct_1m': {
            'label': '>75% H/L in 1 Month',
            'description': 'High-low price variation >75% in 1 month',
            'type': 'boolean',
            'severity': 'high',
            'category': 'volatility',
            'period': '1 month',
            'threshold': '75%',
            'tooltip': 'Extreme intraday/intramonth volatility'
        },
        'hl_150pct_3m': {
            'label': '>150% H/L in 3 Months',
            'description': 'High-low price variation >150% in 3 months',
            'type': 'boolean',
            'severity': 'high',
            'category': 'volatility',
            'period': '3 months',
            'threshold': '150%',
            'tooltip': 'Very high quarterly volatility range'
        },
        'hl_75pct_3m': {
            'label': '>75% H/L in 3 Months',
            'description': 'High-low price variation >75% in 3 months',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'volatility',
            'period': '3 months',
            'threshold': '75%',
            'tooltip': 'High quarterly volatility range'
        },
        'hl_300pct_365d': {
            'label': '>300% H/L in 365 Days',
            'description': 'High-low price variation >300% in 365 days (extreme volatility)',
            'type': 'boolean',
            'severity': 'critical',
            'category': 'volatility',
            'period': '365 days',
            'threshold': '300%',
            'tooltip': 'Extreme annual volatility - stock has seen 4x range between high and low'
        },
        'hl_100pct_6m': {
            'label': '>100% H/L in 6 Months',
            'description': 'High-low price variation >100% in 6 months',
            'type': 'boolean',
            'severity': 'high',
            'category': 'volatility',
            'period': '6 months',
            'threshold': '100%',
            'tooltip': 'Stock has doubled in range between 6-month high and low'
        },
        'hl_200pct_365d': {
            'label': '>200% H/L in 365 Days',
            'description': 'High-low price variation >200% in 365 days (high volatility)',
            'type': 'boolean',
            'severity': 'high',
            'category': 'volatility',
            'period': '365 days',
            'threshold': '200%',
            'tooltip': 'High annual volatility - stock has seen 3x range between high and low'
        },
        'hl_150pct_12m': {
            'label': '>150% H/L in 12 Months',
            'description': 'High-low price variation >150% in 12 months',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'volatility',
            'period': '12 months',
            'threshold': '150%',
            'tooltip': 'Significant annual volatility range'
        }
    }

    # ========== HELPER METHODS ==========

    @classmethod
    def get_all_fields(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all surveillance fields metadata combined.

        Returns:
            Dictionary with table_name.field_name as keys
        """
        all_fields = {}
        for field, meta in cls.SURVEILLANCE_LIST_FIELDS.items():
            all_fields[f"surveillance_list.{field}"] = meta
        for field, meta in cls.FUNDAMENTAL_FLAGS_FIELDS.items():
            all_fields[f"surveillance_fundamental_flags.{field}"] = meta
        for field, meta in cls.PRICE_MOVEMENT_FIELDS.items():
            all_fields[f"surveillance_price_movement.{field}"] = meta
        for field, meta in cls.PRICE_VARIATION_FIELDS.items():
            all_fields[f"surveillance_price_variation.{field}"] = meta
        return all_fields

    @classmethod
    def get_fields_by_category(cls, category: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all fields matching a specific category.

        Args:
            category: Category name (e.g., 'staged_measure', 'binary_flag', 'financial_risk')

        Returns:
            Dictionary of fields in that category
        """
        result = {}
        all_fields = cls.get_all_fields()
        for field_name, meta in all_fields.items():
            if meta.get('category') == category:
                result[field_name] = meta
        return result

    @classmethod
    def get_fields_by_severity(cls, severity: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all fields matching a specific severity level.

        Args:
            severity: Severity level ('low', 'medium', 'high', 'critical')

        Returns:
            Dictionary of fields with that severity
        """
        result = {}
        all_fields = cls.get_all_fields()
        for field_name, meta in all_fields.items():
            if meta.get('severity') == severity:
                result[field_name] = meta
        return result


# Category definitions for grouping fields in UI
SURVEILLANCE_CATEGORIES = {
    'metadata': 'Basic Metadata',
    'staged_measure': 'Staged Surveillance Measures',
    'binary_flag': 'Binary Surveillance Flags',
    'financial_risk': 'Financial Risk Indicators',
    'compliance': 'Compliance Issues',
    'liquidity': 'Liquidity Concerns',
    'valuation': 'Valuation Metrics',
    'short_term_momentum': 'Short-term Price Momentum',
    'medium_term_momentum': 'Medium-term Price Momentum',
    'long_term_momentum': 'Long-term Price Momentum',
    'volatility': 'Price Volatility Indicators'
}

# Severity level definitions for UI styling
SEVERITY_LEVELS = {
    'low': {'color': '#FFA500', 'label': 'Low Risk'},
    'medium': {'color': '#FF8C00', 'label': 'Medium Risk'},
    'high': {'color': '#FF4500', 'label': 'High Risk'},
    'critical': {'color': '#DC143C', 'label': 'Critical Risk'}
}
