<?xml version="1.0"?>
<SMTK_AttributeSystem Version="2">
  <!--**********  Category and Analysis Information ***********-->
  <!--**********  Attribute Definitions ***********-->
  <Definitions>
    <AttDef Type="RemoveOutliersOptions" BaseType="" Version="0" Unique="true">
      <ItemDefinitions>
        <Double Name="sigma" Label="Sigma"> </Double>
      </ItemDefinitions>
    </AttDef>
  </Definitions>
  <!--********** Workflow Views ***********-->
  <Views>
    <View Type="Instanced" Title="Options">
      <InstancedAttributes>
        <Att Name="Options" Type="RemoveOutliersOptions" />
      </InstancedAttributes>
    </View>
  </Views>
</SMTK_AttributeSystem>
