<?xml version="1.0"?>
<SMTK_AttributeSystem Version="2">
  <!--**********  Category and Analysis Information ***********-->
  <!--**********  Attribute Definitions ***********-->
  <Definitions>
    <AttDef Type="ResampleOptions" BaseType="" Version="0" Unique="true">
      <ItemDefinitions>
        <Int Name="period" Label="Period" NumberOfRequiredValues="1">
          <BriefDescription>Resample Frequency</BriefDescription>
            <DiscreteInfo DefaultIndex="0">
              <Value Enum="Daily">0</Value>
              <Value Enum="Weekly">1</Value>
              <Value Enum="Monthly">2</Value>
              <Value Enum="Annualy">3</Value>
            </DiscreteInfo>
        </Int>
        <Int Name="method" Label="Method" NumberOfRequiredValues="1">
          <BriefDescription>Resample Frequency</BriefDescription>
            <DiscreteInfo DefaultIndex="1">
              <Value Enum="Sum">0</Value>
              <Value Enum="Mean">1</Value>
              <Value Enum="Std">2</Value>
              <Value Enum="Max">3</Value>
              <Value Enum="Min">4</Value>
              <Value Enum="Median">5</Value>
            </DiscreteInfo>
        </Int>
      </ItemDefinitions>
    </AttDef>
  </Definitions>
  <!--********** Workflow Views ***********-->
  <Views>
    <View Type="Instanced" Title="Options">
      <InstancedAttributes>
        <Att Name="Options" Type="ResampleOptions" />
      </InstancedAttributes>
    </View>
  </Views>
</SMTK_AttributeSystem>
