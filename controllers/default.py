# -*- coding: utf-8 -*-

def index():
    return dict(message=T('Hello World'))

def error(message = 'Document not found!'):
    session.flash = message
    redirect(URL('index'))

@auth.requires_login()
def manage_organizations():
    db.organization.owner_id.default=auth.user.id    
    db.organization.parent_organization.requires=IS_EMPTY_OR(IS_IN_DB(
            db(db.organization.owner_id==auth.user.id),db.organization,'%(name)s'))
    db.organization._after_insert.append(lambda row, id, uid=auth.user.id:\
        db.membership.insert(organization_id=id,
                             member_id=uid,
                             approved=True,
                             membership_type='manager'))
    grid = SQLFORM.grid(db.organization.owner_id==auth.user.id,
                        links=[lambda row: A('visit',_href=URL('visit',args=row.id))])
    return locals()
response.menu.append(('Organization',None,URL('manage_organizations')))

def visit():
    organization = db.organization(request.args(0,cast=int)) or error()
    membership = db.membership(organization_id=organization.id,
                               member_id=auth.user_id,approved=True)
    if not organization.public_access and not membership: error('Not Authorized')
    links = [
        A('Apply',_class='btn',_href=URL('apply',args=organization.id)),
        A('New Proposal',_class='btn',_href=URL('make_proposal',args=organization.id))
        ]
    return locals()

def apply():
    organization = db.organization(request.args(0,cast=int)) or error()
    return locals()

def withdraw():
    organization = db.organization(request.args(0,cast=int)) or error()
    return locals()

@auth.requires_login()
def make_proposal():
    organization = db.organization(request.args(0,cast=int)) or error()
    membership = db.membership(organization_id=organization.id,approved=True,
                               member_id=auth.user_id,voting_member=True)
    if not membership: error('Not Authorized')
    db.proposal.organization_id.default = organization.id
    form = SQLFORM(db.proposal).process()
    if form.accepted:
        redirect(URL('proposal',args=form.vars.id))
    return locals()

@auth.requires_login()
def proposal():
    links = []
    proposal = db.proposal(request.args(0,cast=int)) or error()
    if proposal.status=='discussion' and request.args(1)=='start_voting':
        proposal.update_record(status='voting')
    if proposal.status=='pending':
        links = [A('move',callback = URL('move_callback',args=proposal.id))]
    elif proposal.status=='moved':
        links = [A('second',callback = URL('second_callback',args=proposal.id))]
    elif proposal.status=='discussion':
        links = [A('propose_amendament',_href = URL('proposal_amendament',args=proposal.id)),
                 A('start voting',_href=URL(args=(proposal.id,'start_voting')))]
    elif proposal.status=='voting':
        links = [A('infavor', callback = URL('vote_callback',args=(proposal.id,'infavor'))),
                 A('opposed', callback = URL('vote_callback',args=(proposal.id,'infavor'))),
                 A('approved', callback = '#'),
                 A('denied', callback = '#')]
    links.append(A('closed', callback = '#'))
    links.append(A('widthdraw', callback = '#'))
    return locals()
        
                 

@auth.requires_login()
def propose_amendament():
    proposal = db.proposal(request.args(0,cast=int)) or error()
    membership = db.membership(organization_id=proposal.organization_id,approved=True,
                               member_id=auth.user_id,voting_member=True)
    if not membership: error('Not Authorized')
    if proposal.status!='discussion' or proposal.amedaments_pending:
        form = None
    else:
        db.proposal.organization_id.default = proposal.organization_id
        db.proposal.parent_id.default = proposal.id
        form = SQLFORM(db.proposal).process()
        if form.accepted:
            proposal.amedaments_pending = True
    return locals()

@auth.requires_login()
def move_callback():
    proposal = db.proposal(request.args(0,cast=int)) or error()
    membership = db.membership(organization_id=proposal.organization_id,approved=True,
                               member_id=auth.user_id,voting_member=True)
    if not membership: raise HTTP(404)
    if proposal.status=='pending' and request.env.request_method=='POST':
        proposal.update_record(status='moved', seconded_by=auth.user.id)
    return proposal.status

@auth.requires_login()
def second_callback():
    proposal = db.proposal(request.args(0,cast=int)) or error()
    membership = db.membership(organization_id=proposal.organization_id,approved=True,
                               member_id=auth.user_id,voting_member=True)
    if not membership: raise HTTP(404)
    if proposal.status=='moved' and request.env.request_method=='POST':
        proposal.update_record(status='discussion', seconded_by=auth.user.id)
    return proposal.status

@auth.requires_login()        
def vote_callback():
    proposal = db.proposal(request.args(0,cast=int)) or error()
    membership = db.membership(organization_id=proposal.organization_id,approved=True,
                               member_id=auth.user_id,voting_member=True)
    if not membership: raise HTTP(404)
    if proposal.status=='voting':
        if request.env.request_method=='POST' and \
                not auth.user.id in (proposal.infavor or [])+(proposal.opposed or []):
            if request.args(1)=='infavor':
                proposal.update_record(infavor=(proposal.infavor or [])+[auth.user.id])
            elif request.args(1)=='opposed':
                proposal.update_record(infavor=(proposal.opposed or [])+[auth.user.id])
    if auth.user.id in proposal.infavor: return 'infavor'
    if auth.user.id in proposal.opposed: return 'opposed'
    return 'abstaned'

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
