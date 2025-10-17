from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Tenant(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_user')
    job_title = models.CharField(max_length=50, blank=True, null=True)
    EMPLOYMENT_STATUS_CHOICES = [
        ('full-time', 'Full-Time'),
        ('part-time', 'Part-Time'),
        ('self-employed', 'Self-Employed'),
        ('unemployed', 'Unemployed'),
        ('student', 'Student'),
        ('retired', 'Retired'),
    ]
    employment_status = models.CharField(max_length=20, blank=True, null=True, choices=EMPLOYMENT_STATUS_CHOICES)
    INDUSTRY_CHOICES = [
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('other', 'Other'),
    ]
    industry = models.CharField(max_length=20, blank=True, null=True, choices=INDUSTRY_CHOICES)
    INCOME_RANGE_CHOICES = [
        ('<$50,000', '<$50,000'),
        ('$50,000-$70,000', '$50,000-$70,000'),
        ('$70,000-$90,000', '$70,000-$90,000'),
        ('>$90,000', '>$90,000'),
    ]
    income_range = models.CharField(max_length=30, blank=True, null=True, choices=INCOME_RANGE_CHOICES)
    mortgage_amount = models.CharField(max_length=50, blank=True, null=True)
    CREDIT_SCORE_RANGE_CHOICES = [
        ('500-600', '500-600'),
        ('600-700', '600-700'),
        ('700-750', '700-750'),
        ('750+', '750+'),
    ]
    credit_score_range = models.CharField(max_length=15, blank=True, null=True, choices=CREDIT_SCORE_RANGE_CHOICES)
    debt_to_income_ratio = models.CharField(max_length=25, blank=True, null=True)
    INVESTMENT_PREFERENCES_CHOICES = [
        ('stocks', 'Stocks'),
        ('real_estate', 'Real Estate'),
        ('cryptocurrencies', 'Cryptocurrencies'),
        ('bonds', 'Bonds'),
    ]
    investment_preferences = models.JSONField(blank=True, null=True, default=list)
    PROPERTY_TYPE_CHOICES = [
        ('renting', 'Renting'),
        ('owning', 'Owning'),
        ('living_with_family/friends', 'Living with Family/Friends'),
    ]
    property_type = models.CharField(max_length=30, blank=True, null=True, choices=PROPERTY_TYPE_CHOICES)
    LENGTH_OF_STAY_CHOICES = [
        ('less_than_1_year', 'Less than 1 year'),
        ('1-3 years', '1-3 years'),
        ('3-5 years', '3-5 years'),
        ('5+ years', '5+ years'),
    ]
    length_of_stay = models.CharField(max_length=20, blank=True, null=True, choices=LENGTH_OF_STAY_CHOICES)
    UTILITY_COST_ESTIMATES_CHOICES = [
        ('<$100', '<$100'),
        ('$100-$200', '$100-$200'),
        ('$200-$500', '$200-$500'),
        ('>$300', '>$300'),
    ]
    utility_cost_estimates = models.CharField(max_length=20, blank=True, null=True, choices=UTILITY_COST_ESTIMATES_CHOICES)
    lease_term = models.IntegerField(blank=True, null=True)
    PREFERRED_RENTAL_PRICE_RANGE_CHOICES = [
        ('$1000-$1500', '$1000-$1500'),
        ('$1500-$2000', '$1500-$2000'),
        ('$2000-$2500', '$2000-$2500'),
        ('$2500+', '$2500+'),
    ]
    preferred_rental_price_range = models.CharField(max_length=20, blank=True, null=True, choices=PREFERRED_RENTAL_PRICE_RANGE_CHOICES)
    current_home_value = models.CharField(max_length=50, blank=True, null=True)
    INTEREST_IN_MOVING_CHOICES = [
        ('within_6_months', 'Yes, in the next 6 months'),
        ('not_planning_to_move', 'No, not planning to move'),
    ]
    interest_in_moving = models.CharField(max_length=50, blank=True, null=True, choices=INTEREST_IN_MOVING_CHOICES)
    LATE_BILL_PAYMENT_HISTORY_CHOICES = [
        ('never', 'Never Missed a Payment'),
        ('occasionally', 'Occasionally Late (1-2 times a year)'),
        ('frequently', 'Frequently Late (3+ times a year)'),
    ]
    late_bill_payment_history = models.CharField(max_length=50, blank=True, null=True, choices=LATE_BILL_PAYMENT_HISTORY_CHOICES)
    SPENDING_HABITS_CHOICES = [
        ('strict', 'I stick to a strict budget'),
        ('moderate', 'I track spending but make occasional impulse buys'),
        ('flexible', 'I spend freely and adjust as needed'),
    ]
    spending_habits = models.CharField(max_length=50, blank=True, null=True, choices=SPENDING_HABITS_CHOICES)
    monthly_budget_allocations = models.CharField(max_length=50, blank=True, null=True)
    FINANCIAL_GOALS_CHOICES = [
        ('pay_off_debt', 'Pay Off Debt'),
        ('build_an_emergency_fund', 'Build an Emergency Fund'),
        ('increase_investments', 'Increase Investments'),
    ]
    financial_goals = models.CharField(max_length=50, blank=True, null=True, choices=FINANCIAL_GOALS_CHOICES)
    ai_for_suggestions = models.BooleanField(default=False)

    page_saved = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"Tenant {self.user_id}"
