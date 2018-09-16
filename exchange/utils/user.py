def has_social_account(user) -> bool:
    return user.is_authenticated and user.socialaccount_set.exists()
