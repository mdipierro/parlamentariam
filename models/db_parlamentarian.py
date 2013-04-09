db.define_table(
    'organization',
    Field('name'),
    Field('owner_id','reference auth_user',default=auth.user_id,readable=False,writable=False),
    Field('parent_organization','reference organization'),
    Field('public_listed','boolean',default=True),
    Field('public_access','boolean',default=False),
    Field('public_discussion','boolean',default=False),
    Field('anyone_can_apply','boolean',default=False),
    auth.signature)

db.define_table(
    'membership',
    Field('member_id','reference auth_user'),
    Field('organization_id','reference organization'),
    Field('voting_member','boolean',default=True),
    Field('membership_type'),
    Field('approved','boolean',default=False),
    auth.signature)

PROPOSAL_WORKFLOW = (
    'pending','moved','discussion','voting','closed','withdrawn','approved','denied')

db.define_table(
    'proposal',
    Field('organization_id','reference organization',readable=False,writable=False),
    Field('name'),
    Field('description'),
    Field('tags','list:string'),
    Field('anonymous_votes','boolean',default=False),
    Field('status',requires=IS_IN_SET(PROPOSAL_WORKFLOW),default='pending',
          readable=False,writable=False),
    Field('seconded_by','reference auth_user',readable=False,writable=False),
    Field('parent_id','reference proposal',readable=False,writable=False),
    Field('pending_amendaments','boolean',default=False,readable=False,writable=False),
    Field('followers','list:reference auth_user',readable=False,writable=False),
    Field('infavor','list:reference auth_user',readable=False,writable=False),
    Field('opposed','list:reference auth_user',readable=False,writable=False),
    auth.signature)

db.define_table(
    'post',                
    Field('proposal','reference proposal'),
    Field('parent_id','reference post'),
    Field('body'),
    auth.signature)
