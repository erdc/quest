<?xml version="1.0"?>
<SMTK_AttributeSystem Version="2">
  <!--**********  Category and Analysis Information ***********-->
  <!--**********  Attribute Definitions ***********-->
  <Definitions>
    <AttDef Type="TimeSeriesOptions" BaseType="" Version="0" Unique="true">
      <ItemDefinitions>
        <String Name="DateTime" Label="Specify as:" Version="0" NumberOfRequiredValues="1">
          <ChildrenDefinitions>
            <String Name="start" Label="Start Date" Optional="true" IsEnabledByDefault="true">
              <BriefDescription>Format yyyy-mm-dd</BriefDescription>
            </String>
            <String Name="end" Label="End Date" Optional="true" IsEnabledByDefault="true">
              <BriefDescription>Format yyyy-mm-dd</BriefDescription>
            </String>
            <String Name="period" Label="Period">
            </String>
          </ChildrenDefinitions>
          <DiscreteInfo DefaultIndex="0">
            <Structure>
              <Value Enum="Start/End Dates">dates</Value>
              <Items>
                <Item>start</Item>
                <Item>end</Item>
              </Items>
            </Structure>
            <Structure>
              <Value Enum="Time Period">period</Value>
              <Items>
                <Item>period</Item>
              </Items>
            </Structure>
          </DiscreteInfo>
        </String>
      </ItemDefinitions>
    </AttDef>
  </Definitions>
  <!--********** Workflow Views ***********-->
  <Views>
    <View Type="Instanced" Title="Options">
      <InstancedAttributes>
        <Att Name="Options" Type="TimeSeriesOptions" />
      </InstancedAttributes>
    </View>
  </Views>
</SMTK_AttributeSystem>
