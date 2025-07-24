using System;

namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class TenantUpdateModel
   {
      public TenantUpdateModel()
      {
         TenantID = -1;
         UpdateUserID = -1;
      }
      public int TenantID { get; set; }
      public string FirstName { get; set; }
      public string LastName { get; set; }
      public string Comment { get; set; }
      public DateTime UpdateDate { get; set; }
      public int UpdateUserID { get; set; }
   }
}
