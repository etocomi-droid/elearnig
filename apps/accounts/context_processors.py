from apps.accounts.models import ProjectMember


def project_permissions(request):
    """テンプレートに権限情報を渡すコンテキストプロセッサ"""
    perms = {
        'can_manage_funnels': True,
        'can_manage_emails': True,
        'can_manage_members': True,
        'can_manage_contacts': True,
        'can_manage_products': True,
        'can_manage_bookings': True,
        'is_project_owner': False,
        'is_project_admin': False,
    }

    project = getattr(request, 'current_project', None)
    if not project or not request.user.is_authenticated:
        return {'project_perms': perms}

    user = request.user

    # オーナーは全権限
    if project.owner == user:
        perms['is_project_owner'] = True
        perms['is_project_admin'] = True
        return {'project_perms': perms}

    # メンバーの権限を取得
    try:
        member = ProjectMember.objects.get(project=project, user=user)
        if member.role == 'admin':
            perms['is_project_admin'] = True
        else:
            # operatorの場合は個別権限をチェック
            perms['can_manage_funnels'] = member.can_manage_funnels
            perms['can_manage_emails'] = member.can_manage_emails
            perms['can_manage_members'] = member.can_manage_members
            perms['can_manage_contacts'] = member.can_manage_contacts
            perms['can_manage_products'] = member.can_manage_products
            perms['can_manage_bookings'] = member.can_manage_bookings
    except ProjectMember.DoesNotExist:
        # メンバーでない場合は全権限なし
        for key in perms:
            if key.startswith('can_'):
                perms[key] = False

    return {'project_perms': perms}
