using System;

namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class LeaseRenewalModel
   {
      public int LeaseRenewalID { get; set; }
      public int ParentLeaseID { get; set; }
      public int UnitID { get; set; }
      public int Length { get; set; }
      public DateTime? SignDate { get; set; }
      public DateTime? StartDate { get; set; }
      public DateTime? EndDate { get; set; }
      public decimal DefaultCommercialExpensePercentage { get; set; }
      public decimal DefaultCommercialExpenseAdminPercentage { get; set; }
      public int DocumentID { get; set; }
      public DateTime CreateDate { get; set; }
      public int CreateUserID { get; set; }
      public DateTime UpdateDate { get; set; }
      public int UpdateUserID { get; set; }
   }
}
