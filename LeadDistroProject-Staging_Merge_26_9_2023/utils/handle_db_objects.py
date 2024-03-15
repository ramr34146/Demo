from dashboard.models import LeadsDistribution

#use for helping purpose
def getMemberRemainingLeadsLimit(team_user, superuser):
    leads_data = LeadsDistribution.objects.filter(assign_to=team_user, lead__superuser=superuser).count()
    return leads_data


#check if agent got that lead already
def checkAgentLeadAlreadyExist(number, team_user, superuser_obj):
    res = LeadsDistribution.objects.filter(
        assign_to = team_user,
        lead__phone =number,
        lead__superuser = superuser_obj
    ).count()
    if res > 0:
        return True 
    return False
    