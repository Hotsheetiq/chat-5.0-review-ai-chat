using System;
using System.Collections.Generic;

namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class LeaseModel
   {
      public int LeaseID { get; set; }
      public int UnitID { get; set; }
      public int TenantID { get; set; }
      public bool IsCommercial { get; set; }
      public DateTime MoveInDate { get; set; }
      public DateTime MoveOutDate { get; set; }
      public DateTime ExpectedMoveOutDate { get; set; }
      public DateTime NoticeDate { get; set; }
      public int SortOrder { get; set; }
      public List<LeaseRenewalModel> LeaseRenewals { get; set; }
      public int CreateUserID { get; set; }
      public int UpdateUserID { get; set; }
   }
}
